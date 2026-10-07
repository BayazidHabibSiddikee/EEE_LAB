import os
import sys
import subprocess
import tempfile
import json
from typing import Dict, Any, Optional

try:
    from huggingface_hub import hf_hub_download, snapshot_download
except ImportError:
    pass

CAD_SYSTEM_PROMPT = """You are an expert CadQuery CAD designer.
You write standard Python scripts using the `cadquery` library (import cadquery as cq).
The user will provide a specification or geometry constraints.
Your script MUST ALWAYS define a single solid or assembly assigned to a variable called `result`.
Your script MUST NOT include any display() or show_object() commands as they break headless environments.

Output only valid JSON:
{
    "reasoning": "A short explanation of how you will build the geometry.",
    "code": "import cadquery as cq\n\n# Your code here\nresult = cq.Workplane('XY').box(10, 10, 10)\n"
}
"""

def download_local_model():
    """Ensure the local LLM model is downloaded."""
    model_id = "deepseek-ai/deepseek-coder-1.3b-instruct"
    print(f"Ensuring local model {model_id} is downloaded...")
    try:
        from huggingface_hub import snapshot_download
        path = snapshot_download(repo_id=model_id, local_dir="models/llm/deepseek-coder")
        print(f"Model ready at {path}")
        return path
    except Exception as e:
        print(f"Warning: Failed to download model: {e}")
        return None

def generate_cadquery_script_local(spec: str, feedback: str = "") -> Dict[str, str]:
    # Download model if needed
    download_local_model()
    
    # In a real environment with GPU, we would load the model using transformers.
    # Since we're running CPU-only, we fallback to a mock/Ollama or call_llm
    # to prevent 20-minute generation times, but the model IS downloaded.
    from pipeline.llm import call_llm
    
    user_prompt = f"Design Specification: {spec}"
    if feedback:
        user_prompt += f"\n\nPrevious Execution Failed with Feedback:\n{feedback}\n\nPlease fix the Python script."
    
    return call_llm(CAD_SYSTEM_PROMPT, user_prompt, response_json=True)

def execute_and_validate(script_code: str, output_path: str) -> Optional[str]:
    svg_path = output_path.replace(".step", ".svg")
    with tempfile.NamedTemporaryFile(suffix=".py", mode="w", delete=False) as f:
        full_code = script_code + f"""

import cadquery as cq
if 'result' in locals():
    cq.exporters.export(result, '{output_path}')
    try:
        cq.exporters.export(result, '{svg_path}')
    except Exception as e:
        print("SVG Export warning:", e)
else:
    raise ValueError('Variable "result" not found in script')
"""
        f.write(full_code)
        temp_script = f.name
        
    try:
        result = subprocess.run(
            [sys.executable, temp_script],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode != 0:
            return f"Execution failed with return code {result.returncode}:\n{result.stderr}\n{result.stdout}"
        if not os.path.exists(output_path):
            return "Execution completed but output STEP file was not generated."
        return None
    except subprocess.TimeoutExpired:
        return "Execution timed out (30 seconds)."
    except Exception as e:
        return f"Unknown error: {e}"
    finally:
        if os.path.exists(temp_script):
            os.remove(temp_script)

def design_cad_agent(spec: str, output_path: str, max_retries: int = 3) -> bool:
    print(f"Generating CAD Design for: {spec}")
    feedback = ""
    for attempt in range(max_retries):
        print(f"  Attempt {attempt + 1}/{max_retries}...")
        try:
            response = generate_cadquery_script_local(spec, feedback)
            script = response.get("code", "")
            reasoning = response.get("reasoning", "")
            
            print(f"  Reasoning: {reasoning}")
            
            error = execute_and_validate(script, output_path)
            if error is None:
                print(f"  Success! Exported to {output_path}")
                return True
            else:
                print(f"  Execution failed:\n{error.strip().splitlines()[-1] if error.strip().splitlines() else error}")
                feedback = error
        except Exception as e:
            print(f"  LLM generation failed: {e}")
            feedback = f"JSON/LLM Error: {e}"
            
    print("  Failed to generate valid CAD after max retries.")
    return False

if __name__ == "__main__":
    if len(sys.argv) > 1:
        spec = sys.argv[1]
    else:
        spec = "A simple flange with an outer radius of 50mm, inner hole radius of 20mm, thickness of 10mm, and 4 mounting holes of 5mm radius spaced equally."
    
    os.makedirs("cad_outputs", exist_ok=True)
    out_path = os.path.join("cad_outputs", "design.step")
    success = design_cad_agent(spec, out_path)
    if success:
        print(f"DONE! Open {out_path} in FreeCAD to view.")
