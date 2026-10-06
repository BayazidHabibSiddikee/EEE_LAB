import argparse
import os
import datetime
import subprocess
import json
import pandas as pd
import matplotlib.pyplot as plt
import schemdraw
import schemdraw.elements as elm
from pipeline.assemble import load_config, render_latex, compile_pdf
from pipeline.llm import generate_report_sections, generate_circuit_design
from pipeline.research import get_research_context, save_research_context
from pipeline.verify import run_all_checks, write_report, extract_features

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

    netlist_content = f"Dynamic Circuit: {exp_name}\\n"
    model_path = os.path.abspath("models/triac.sub").replace('\\', '/')
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

def _build_data_table_from_simulation(txt_out: str) -> str:
    try:
        df = pd.read_csv(txt_out, sep=r'\s+', header=None)
        if df.shape[1] >= 4:
            v = pd.concat([df[0], df[2]]).reset_index(drop=True)
            i = pd.concat([df[1], df[3]]).reset_index(drop=True)
        else:
            v = df[0]
            i = df[1]

        v_sorted, i_sorted = zip(*sorted(zip(v, i)))
        v_sorted = list(v_sorted)
        i_sorted = list(i_sorted)

        n_points = min(10, len(v_sorted))
        indices = [int(j * (len(v_sorted) - 1) / (n_points - 1)) for j in range(n_points)]

        rows = []
        for idx in indices:
            v_val = v_sorted[idx]
            i_val = i_sorted[idx] * 1000
            rows.append(f"        {v_val:.1f} & {i_val:.1f} \\\\")

        table = f"""\\begin{{table}}[H]
    \\centering
    \\begin{{tabular}}{{|c|c|}}
        \\hline
        \\textbf{{Voltage (V)}} & \\textbf{{Current (mA)}} \\\\
        \\hline
{chr(10).join(rows)}
        \\hline
    \\end{{tabular}}
    \\caption{{Simulated Data (Sample Points)}}
\\end{{table}}"""
        return table
    except Exception as e:
        print(f"Error building data table: {e}")
        return ""

def run_generation(args, settings):
    slug = args.name.lower().replace(" ", "_")
    run_dir = os.path.join("runs", slug)
    os.makedirs(run_dir, exist_ok=True)
    os.makedirs(os.path.join(run_dir, "figs"), exist_ok=True)
    os.makedirs(os.path.join(run_dir, "sim"), exist_ok=True)

    print(f"--- Running LabGen for: {args.name} ---")

    print("Running LangGraph pipeline...")
    from pipeline.graph import run_pipeline

    circuit_prompt = args.circuit_prompt if args.circuit_prompt else ""

    graph_result = run_pipeline(args.name, circuit_prompt)
    circuit_json = graph_result.get("circuit_json", {})
    llm_sections = graph_result.get("report_sections", {})

    print("Executing dynamic circuit...")
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

    research_context = get_research_context(args.name)
    save_research_context(run_dir, args.name, research_context)

    data_table_latex = _build_data_table_from_simulation(txt_out)

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
        "data_table_latex": data_table_latex,
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
        "circuit_img": os.path.abspath(schem_path).replace('\\\\', '/') if schem_path else "",
        "theory_img": os.path.abspath(theory_img_path).replace('\\\\', '/') if theory_img_path else "",
        "plots": [
            {"path": os.path.abspath(plot_path).replace('\\\\', '/') if plot_path else "", "caption": f"Simulated {args.name} Curve"}
        ]
    }

    pdf_filename = f"Exp_{args.exp:02d}_{slug}.tex"
    tex_out = os.path.join(run_dir, pdf_filename)
    render_latex(os.path.join("templates", "report.tex.j2"), tex_out, context)

    compile_pdf(tex_out, run_dir)

    if settings.get("verification", {}).get("enabled", True):
        print("Running verification...")
        report_bundle = {
            "experiment_name": args.name,
            "sections": sections,
            "circuit_json": circuit_json,
            "iv_data_path": txt_out,
            "research_context": research_context,
            "settings": settings,
            "plots": context["plots"]
        }
        results = run_all_checks(report_bundle)
        write_report(results, os.path.join(run_dir, "verification_report.json"))

    print("Done!")

def run_verification(args, settings):
    if args.input.endswith(".pdf"):
        from pipeline.ingest import extract_pdf
        print(f"Extracting PDF: {args.input}")
        extracted = extract_pdf(args.input)
        if "error" in extracted:
            print(f"Error: {extracted['error']}")
            return

        sections = extracted.get("sections", {})
        latex_table = extracted.get("latex_table", "")
        if latex_table:
            sections["data_table_latex"] = latex_table

        report_bundle = {
            "experiment_name": args.experiment or "Unknown",
            "sections": sections,
            "circuit_json": {},
            "iv_data_path": args.data if args.data and os.path.exists(args.data) else "",
            "research_context": "",
            "settings": settings,
            "plots": []
        }
    else:
        run_dir = args.input
        tex_file = None
        for f in os.listdir(run_dir):
            if f.endswith(".tex"):
                tex_file = os.path.join(run_dir, f)
                break
        if not tex_file:
            print("No .tex file found in run directory")
            return

        with open(tex_file, "r") as f:
            tex_content = f.read()

        import re
        sections = {}
        section_matches = re.findall(r"\\section\{([^}]+)\}(.*?)(?=\\section|\\end\{document\})", tex_content, re.DOTALL)
        for name, content in section_matches:
            sections[name.lower().replace(" ", "_")] = content.strip()

        table_match = re.search(r"\\begin\{table\}.*?\\end\{table\}", tex_content, re.DOTALL)
        if table_match:
            sections["data_table_latex"] = table_match.group(0)

        iv_path = os.path.join(run_dir, "iv_data.txt")
        if not os.path.exists(iv_path) and args.data:
            iv_path = args.data

        research_path = os.path.join(run_dir, "research_context.json")
        research_context = ""
        if os.path.exists(research_path):
            with open(research_path, "r") as f:
                research_context = json.load(f).get("context", "")

        circuit_json = {}
        circuit_path = os.path.join(run_dir, "dynamic.cir")
        if os.path.exists(circuit_path):
            pass

        report_bundle = {
            "experiment_name": args.experiment or "Unknown",
            "sections": sections,
            "circuit_json": circuit_json,
            "iv_data_path": iv_path,
            "research_context": research_context,
            "settings": settings,
            "plots": []
        }

    print("Running verification...")
    results = run_all_checks(report_bundle)

    print(json.dumps(results, indent=2))

    if args.output:
        write_report(results, args.output)
    else:
        out_path = os.path.join(os.path.dirname(args.input), "verification_report.json") if not args.input.endswith(".pdf") else args.input.replace(".pdf", "_verification.json")
        write_report(results, out_path)

def main():
    parser = argparse.ArgumentParser(description="LabGen - EEE Lab Report Generator & Verifier")
    subparsers = parser.add_subparsers(dest="command", required=True)

    gen_parser = subparsers.add_parser("generate", help="Generate lab report")
    gen_parser.add_argument("name", help="Name of the experiment")
    gen_parser.add_argument("circuit_prompt", nargs="?", default="", help="Prompt describing circuit connections")
    gen_parser.add_argument("--exp", type=int, default=2, help="Experiment number")

    verify_parser = subparsers.add_parser("verify", help="Verify lab report")
    verify_parser.add_argument("input", help="Path to PDF, .tex file, or run directory")
    verify_parser.add_argument("--experiment", help="Experiment name (for PDF verification)")
    verify_parser.add_argument("--data", help="Path to iv_data.txt for data cross-check")
    verify_parser.add_argument("--output", help="Output path for verification report")

    args = parser.parse_args()

    settings_path = os.path.join(os.path.dirname(__file__), "settings.json")
    with open(settings_path, "r") as f:
        settings = json.load(f)

    api_key = settings.get("llm", {}).get("api_key")
    if not api_key or api_key == "YOUR_API_KEY":
        if os.environ.get("GEMINI_API_KEY"):
            api_key = os.environ.get("GEMINI_API_KEY")
        else:
            print("Error: Please configure your API key in settings.json or export GEMINI_API_KEY.")
            return
    os.environ["GEMINI_API_KEY"] = api_key

    if args.command == "generate":
        run_generation(args, settings)
    elif args.command == "verify":
        run_verification(args, settings)

if __name__ == "__main__":
    main()