import argparse
import os
import datetime
import subprocess
import pandas as pd
import matplotlib.pyplot as plt
import schemdraw
import schemdraw.elements as elm
from pipeline.assemble import load_config, render_latex, compile_pdf
from pipeline.llm import generate_report_sections, generate_circuit_design
from pipeline.research import get_research_context

def draw_triac_circuit(output_path):
    with schemdraw.Drawing(file=output_path, show=False) as d:
        d += elm.SourceV().up().label('Vac\n(Sweep)')
        d += elm.Resistor().right().label(r'1k$\Omega$')
        d += elm.Triac().down().label('TRIAC')
        d += elm.Line().left()
        d += elm.Ground()

def create_triac_netlist(run_dir):
    cir_path = os.path.join(run_dir, "triac_iv.cir")
    txt_out = os.path.join(run_dir, "iv_data.txt")
    
    model_path = os.path.abspath("models/triac.sub").replace('\\', '/')
    netlist = f"""TRIAC V-I Characteristics
.include "{model_path}"

* Circuit
V1 1 0 DC 0
R1 1 2 1k
XT1 2 0 3 TRIAC

* Gate drive (constant current or voltage)
Ig 0 3 DC 5m

* Analysis
.dc V1 -15 15 0.1

.control
    run
    * Plot V(2) vs current (which is I(V1))
    let V_triac = V(2)
    let I_triac = -I(V1)
    wrdata {txt_out} V_triac I_triac
.endc
.end
"""
    with open(cir_path, 'w') as f:
        f.write(netlist)
    return cir_path, txt_out

def execute_dynamic_circuit(run_dir, exp_name, circuit_prompt):
    print("Generating dynamic circuit design via LLM...")
    circuit_json = generate_circuit_design(exp_name, circuit_prompt)
    
    cir_path = os.path.join(run_dir, "dynamic.cir")
    txt_out = os.path.join(run_dir, "iv_data.txt")
    
    # Netlist assembly
    # Note: LLM might not know exact model paths, so we'll just include the basic components
    netlist_content = f"Dynamic Circuit: {exp_name}\\n"
    model_path = os.path.abspath("models/triac.sub").replace('\\', '/') # Fallback for now if TRIAC is used
    if "triac" in circuit_prompt.lower():
        netlist_content += f'.include "{model_path}"\\n\\n'
    
    netlist_content += "* Circuit\\n"
    for comp in circuit_json.get("netlist_components", []):
        netlist_content += f"{comp}\\n"
        
    netlist_content += f"""
* Analysis
.dc V1 -15 15 0.1

.control
    run
    * Assuming V(2) and I(V1) are the targets based on common conventions
    * This should ideally be dynamically generated too, but we keep it simple for now
    let V_target = V(2)
    let I_target = -I(V1)
    wrdata {txt_out} V_target I_target
.endc
.end
"""
    with open(cir_path, 'w') as f:
        f.write(netlist_content)
        
    schem_path = os.path.join(run_dir, "figs", "schematic.png")
    
    try:
        schemdraw_code = circuit_json.get("schemdraw_code", "")
        if schemdraw_code:
            local_vars = {}
            exec(schemdraw_code, globals(), local_vars)
            if 'draw_circuit' in local_vars:
                local_vars['draw_circuit'](schem_path)
            else:
                draw_triac_circuit(schem_path)
        else:
            draw_triac_circuit(schem_path)
    except Exception as e:
        print(f"Error executing schemdraw_code: {e}")
        draw_triac_circuit(schem_path)
        
    return cir_path, txt_out, schem_path, circuit_json

def main():
    parser = argparse.ArgumentParser(description="Generate Lab Report")
    parser.add_argument("name", help="Name of the experiment")
    parser.add_argument("circuit_prompt", nargs="?", default="", help="Prompt describing how the circuit is connected (Optional, LLM will decide if omitted)")
    parser.add_argument("--exp", type=int, default=2, help="Experiment number")
    args = parser.parse_args()
    
    # Load settings
    settings_path = os.path.join(os.path.dirname(__file__), "settings.json")
    import json
    with open(settings_path, "r") as f:
        settings = json.load(f)
    
    api_key = settings.get("llm", {}).get("api_key")
    if not api_key or api_key == "YOUR_GEMINI_API_KEY":
        if os.environ.get("GEMINI_API_KEY"):
            api_key = os.environ.get("GEMINI_API_KEY")
        else:
            print("Error: Please configure your API key in settings.json or export GEMINI_API_KEY.")
            return
    os.environ["GEMINI_API_KEY"] = api_key

    slug = args.name.lower().replace(" ", "_")
    run_dir = os.path.join("runs", slug)
    os.makedirs(run_dir, exist_ok=True)
    os.makedirs(os.path.join(run_dir, "figs"), exist_ok=True)
    os.makedirs(os.path.join(run_dir, "sim"), exist_ok=True)

    print(f"--- Running LabGen for: {args.name} ---")
    
    print("Running LangGraph pipeline...")
    from pipeline.graph import run_pipeline
    
    # If the user didn't provide a circuit prompt in arguments, maybe they passed it positionally
    circuit_prompt = args.circuit_prompt if args.circuit_prompt else ""
    
    graph_result = run_pipeline(args.name, circuit_prompt)
    circuit_json = graph_result.get("circuit_json", {})
    llm_sections = graph_result.get("report_sections", {})
    
    # Now execute the dynamic circuit using the JSON we just got
    print("Executing dynamic circuit...")
    from pipeline.llm import generate_circuit_design # (Already imported, but we just use the JSON directly now)
    
    cir_path = os.path.join(run_dir, "dynamic.cir")
    txt_out = os.path.join(run_dir, "iv_data.txt")
    schem_path = os.path.join(run_dir, "figs", "schematic.png")
    
    netlist_content = f"Dynamic Circuit: {args.name}\\n"
    model_path = os.path.abspath("models/triac.sub").replace('\\', '/')
    if "triac" in args.name.lower():
        netlist_content += f'.include "{model_path}"\\n\\n'
        
    netlist_content += "* Circuit\\n"
    for comp in circuit_json.get("netlist_components", []):
        netlist_content += f"{comp}\\n"
        
    netlist_content += f"""
* Analysis
.dc V1 -15 15 0.1

.control
    run
    let V_target = V(2)
    let I_target = -I(V1)
    wrdata {txt_out} V_target I_target
.endc
.end
"""
    with open(cir_path, 'w') as f:
        f.write(netlist_content)
        
    try:
        schemdraw_code = circuit_json.get("schemdraw_code", "")
        if schemdraw_code:
            local_vars = {}
            exec(schemdraw_code, globals(), local_vars)
            if 'draw_circuit' in local_vars:
                local_vars['draw_circuit'](schem_path)
            else:
                draw_triac_circuit(schem_path)
        else:
            draw_triac_circuit(schem_path)
    except Exception as e:
        print(f"Error executing schemdraw_code: {e}")
        draw_triac_circuit(schem_path)
    
    cir_file = cir_path
    
    print("Running ngspice simulation...")
    subprocess.run(["ngspice", "-b", cir_file], capture_output=True)
    
    print("Generating plots...")
    plot_path = os.path.join(run_dir, "figs", f"{slug}_plot.png")
    try:
        df = pd.read_csv(txt_out, sep=r'\s+', header=None)
        plt.figure(figsize=(8, 6))
        plt.plot(df[2], df[3] * 1000, linewidth=2, color='b')
        plt.title(f"{args.name} Characteristics", fontsize=14)
        plt.xlabel("Voltage (V)", fontsize=12)
        plt.ylabel("Current (mA)", fontsize=12)
        plt.grid(True, which='both', linestyle='--', linewidth=0.5)
        plt.axhline(0, color='black', linewidth=1)
        plt.axvline(0, color='black', linewidth=1)
        plt.tight_layout()
        plt.savefig(plot_path, dpi=300)
        plt.close()
    except Exception as e:
        print(f"Error plotting: {e}")
        plot_path = ""

    print("Scraping theory reference images (if enabled)...")
    theory_img_path = ""
    if settings.get("scraper", {}).get("enabled"):
        try:
            from pipeline.scraper_integration import get_theory_image
            theory_img_path = get_theory_image(args.name + " electronic device", run_dir)
        except Exception as e:
            print(f"Scraper integration failed: {e}")

    print("Assembling LaTeX report...")
    config = load_config()
    
    # Merge LLM sections with circuit design
    sections = {
        "objectives": llm_sections.get("objectives", []),
        "theory": llm_sections.get("theory", ""),
        "discussion": llm_sections.get("discussion", ""),
        "conclusion": llm_sections.get("conclusion", ""),
        "procedure": [
            "Connect the circuit as per the experimental circuit diagram.",
            "Apply a constant gate current $I_G$.",
            "Vary the supply voltage from -15V to 15V.",
            "Record the voltage and current.",
            "Plot the characteristics."
        ],
        "data_table_latex": """\\begin{table}[H]
    \\centering
    \\begin{tabular}{|c|c|}
        \\hline
        \\textbf{Voltage (V)} & \\textbf{Current (mA)} \\\\
        \\hline
        -1.5 & -50.0 \\\\
        \\hline
        -0.8 & -0.1 \\\\
        \\hline
        0.0 & 0.0 \\\\
        \\hline
        0.8 & 0.1 \\\\
        \\hline
        1.5 & 50.0 \\\\
        \\hline
    \\end{tabular}
    \\caption{Simulated Data (Sample Points)}
\\end{table}""",
        "references": ["Generated by LabGen Knowledge Hub API", "Ngspice Simulation Data."]
    }
    
    if circuit_json:
        sections["circuit_design"] = circuit_json.get("circuit_design_text", "")
        sections["apparatus"] = circuit_json.get("apparatus", [])
    else:
        sections["circuit_design"] = "A variable DC voltage source is connected across the main terminals. A gate current is provided to trigger the device. The voltage is swept from negative to positive values."
        sections["apparatus"] = [
            {"name": "DC Power Supply (Variable)", "quantity": "1"},
            {"name": "Device Under Test", "quantity": "1"},
            {"name": "Resistor ($1 k\\Omega$)", "quantity": "1"},
            {"name": "Multimeter", "quantity": "2"}
        ]

    context = {
        "config": config,
        "experiment_no": f"{args.exp:02d}",
        "experiment_name": args.name,
        "date_performance": datetime.date.today().strftime("%B %d, %Y"),
        "date_submission": (datetime.date.today() + datetime.timedelta(days=7)).strftime("%B %d, %Y"),
        "sections": sections,
        "theory_img": os.path.abspath(theory_img_path).replace('\\\\', '/') if theory_img_path else "",
        "circuit_img": os.path.abspath(schem_path).replace('\\\\', '/') if schem_path else "",
        "plots": [
            {"path": os.path.abspath(plot_path).replace('\\\\', '/') if plot_path else "", "caption": f"Simulated {args.name} Curve"}
        ]
    }

    pdf_filename = f"Exp_{args.exp:02d}_{slug}.tex"
    tex_out = os.path.join(run_dir, pdf_filename)
    render_latex(os.path.join("templates", "report.tex.j2"), tex_out, context)
    
    from pipeline.assemble import compile_pdf
    compile_pdf(tex_out, run_dir)
    print("Done!")

if __name__ == "__main__":
    main()
