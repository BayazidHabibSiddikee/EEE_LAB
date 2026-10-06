import os
import json
try:
    from google import genai
    from google.genai import types
except ImportError:
    genai = None

def get_client():
    if genai is None:
        raise ImportError("Please install google-genai: pip install google-genai")
    if not os.environ.get("GEMINI_API_KEY"):
        raise ValueError("GEMINI_API_KEY environment variable is missing.")
    return genai.Client()

def generate_report_sections(experiment_name, research_context):
    """
    Calls Gemini to generate the report sections based on the research.
    """
    client = get_client()
    
    prompt_path = os.path.join(os.path.dirname(__file__), "..", "prompts", "system_prompt.txt")
    with open(prompt_path, "r") as f:
        system_prompt = f.read()
        
    user_prompt = f"""
Experiment Name: {experiment_name}

Research Context:
{research_context}

Generate the following sections for the lab report as a JSON object:
{{
    "objectives": ["To ...", "To ..."],
    "theory": "Introduction paragraph 1... \\n\\nIntroduction paragraph 2...",
    "discussion": "Past tense discussion...",
    "conclusion": "Past tense conclusion..."
}}
Ensure you meet the word counts specified in your system instructions.
"""
    
    response = client.models.generate_content(
        model="gemini-2.5-pro", # Or gemini-3.1-pro if available in the SDK
        contents=user_prompt,
        config=types.GenerateContentConfig(
            system_instruction=system_prompt,
            response_mime_type="application/json",
            temperature=0.2,
        ),
    )
    
    text = response.text
    if text.startswith("```json"):
        text = text[7:]
    if text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    return json.loads(text.strip())

def generate_circuit_design(experiment_name, connection_prompt):
    """
    Calls Gemini to design the circuit based on a user connection prompt.
    """
    client = get_client()
    
    user_prompt = f"""
Experiment: {experiment_name}
Connection Instructions: {connection_prompt if connection_prompt else "Design a standard, typical circuit for this experiment."}

You are an expert EEE circuit designer.
Based on the instructions above, provide a JSON representation of the circuit.
We need the component list (Apparatus), a textual description of the circuit design, the ngspice netlist components, and Python code using the `schemdraw` library to draw the circuit.

Return JSON format strictly:
{{
    "circuit_design_text": "Detailed explanation of how the circuit is designed and works.",
    "apparatus": [
        {{"name": "Resistor (1k Ohm)", "quantity": "1"}},
        {{"name": "TRIAC (BT136)", "quantity": "1"}}
    ],
    "netlist_components": [
        "V1 1 0 DC 0",
        "R1 1 2 1k",
        "XT1 2 0 3 TRIAC"
    ],
    "schemdraw_code": "def draw_circuit(output_path):\\n    import schemdraw\\n    import schemdraw.elements as elm\\n    with schemdraw.Drawing(file=output_path, show=False) as d:\\n        d += elm.SourceV().up().label('Vac')\\n        d += elm.Resistor().right().label('1k')\\n        # Add other components...\\n"
}}
Ensure the `schemdraw_code` contains a single function named `draw_circuit(output_path)` that takes the output path and saves the schematic.
"""
    
    response = client.models.generate_content(
        model="gemini-2.5-pro",
        contents=user_prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            temperature=0.1,
        ),
    )
    
    text = response.text
    if text.startswith("```json"):
        text = text[7:]
    if text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    return json.loads(text.strip())
