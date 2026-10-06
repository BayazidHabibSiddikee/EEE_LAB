import os
import jinja2
import subprocess
import shutil

import json

def load_config(config_path="settings.json"):
    # Resolve relative to the labgen directory, not CWD, if needed.
    # main.py runs from labgen usually, but it's safer to use absolute paths based on __file__
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    full_path = os.path.join(base_dir, config_path)
    with open(full_path, 'r') as f:
        settings = json.load(f)
    return settings.get("report", {})

def render_latex(template_path, output_tex_path, context):
    template_dir = os.path.dirname(template_path)
    template_name = os.path.basename(template_path)
    
    # We need to change Jinja's block/variable tags so they don't clash with LaTeX
    # But in the template above, I used {% %} and {{ }} which is standard Jinja.
    # LaTeX uses { } a lot, so maybe standard jinja is ok if we put spaces: {{ var }}
    # Let's see. If it fails, we will adjust the delimiters.
    env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(template_dir),
        block_start_string='{%',
        block_end_string='%}',
        variable_start_string='{{',
        variable_end_string='}}',
        comment_start_string='{#',
        comment_end_string='#}',
        autoescape=False
    )
    
    template = env.get_template(template_name)
    rendered = template.render(**context)
    
    with open(output_tex_path, 'w') as f:
        f.write(rendered)

def compile_pdf(tex_file, output_dir):
    """Compiles the tex file to PDF using tectonic."""
    cmd = ["tectonic", "--outdir", output_dir, tex_file]
    
    print("Compiling LaTeX to PDF using tectonic...")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print("tectonic failed. Output:")
        print(result.stdout)
        print(result.stderr)
        
    pdf_file = tex_file.replace(".tex", ".pdf")
    if os.path.exists(pdf_file):
        print(f"PDF successfully generated: {pdf_file}")
    else:
        print(f"Failed to generate PDF.")
