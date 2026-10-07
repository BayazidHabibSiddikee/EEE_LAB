from mcp.server.fastmcp import FastMCP
import sys
import os

# Ensure labgen modules can be imported
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from pipeline.cad import design_cad_agent

# Initialize FastMCP Server
mcp = FastMCP("LabGen-CAD")

@mcp.tool()
def generate_cad_design(specification: str, output_filename: str = "design.step") -> str:
    """
    Generates a 3D mechanical CAD design (STEP format) based on natural language specification using the local CAD pipeline (Zero-to-CAD).
    
    Args:
        specification: The natural language geometric constraints and description of the mechanical part (e.g., "A flange with 50mm radius").
        output_filename: The name of the output STEP file (default: design.step).
    """
    out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cad_outputs")
    os.makedirs(out_dir, exist_ok=True)
    
    if not output_filename.endswith(".step"):
        output_filename += ".step"
        
    out_path = os.path.join(out_dir, output_filename)
    
    success = design_cad_agent(specification, out_path)
    if success:
        svg_path = out_path.replace(".step", ".svg")
        return f"Successfully generated CAD design.\nSTEP File: {out_path}\nSVG File: {svg_path}"
    else:
        return "Failed to generate CAD design. Check internal pipeline logs for CadQuery execution errors."

if __name__ == "__main__":
    mcp.run()
