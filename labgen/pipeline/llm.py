import os
import json
import requests
from typing import Dict, Any

def get_llm_config() -> Dict[str, Any]:
    settings_path = os.path.join(os.path.dirname(__file__), "..", "settings.json")
    with open(settings_path, "r") as f:
        settings = json.load(f)
    return settings.get("llm", {})

def call_llm(system_prompt: str, user_prompt: str, response_json: bool = True) -> Dict[str, Any]:
    config = get_llm_config()
    provider = config.get("provider", "custom")
    base_url = config.get("base_url", "")
    api_key = config.get("api_key", "")
    model = config.get("model", "gemini-2.5-pro")
    temperature = config.get("temperature", 0.2)
    
    if not api_key or api_key == "YOUR_API_KEY":
        if os.environ.get("GEMINI_API_KEY"):
            api_key = os.environ.get("GEMINI_API_KEY")
        else:
            raise ValueError("No API key configured in settings.json or GEMINI_API_KEY env var")
    
    headers = {"Content-Type": "application/json"}
    
    if "openai" in base_url or "localhost" in base_url or "127.0.0.1" in base_url or provider == "openai":
        # OpenAI-compatible API
        headers["Authorization"] = f"Bearer {api_key}"
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": temperature,
        }
        if response_json:
            payload["response_format"] = {"type": "json_object"}
        
        resp = requests.post(f"{base_url}/chat/completions", headers=headers, json=payload, timeout=120)
        resp.raise_for_status()
        data = resp.json()
        text = data["choices"][0]["message"]["content"]
    
    elif "generativelanguage" in base_url or provider == "gemini":
        # Google Gemini API
        headers = {"Content-Type": "application/json", "x-goog-api-key": api_key}
        payload = {
            "contents": [{"parts": [{"text": user_prompt}]}],
            "systemInstruction": {"parts": [{"text": system_prompt}]},
            "generationConfig": {"temperature": temperature, "responseMimeType": "application/json" if response_json else "text/plain"}
        }
        resp = requests.post(f"{base_url}/models/{model}:generateContent", headers=headers, json=payload, timeout=120)
        resp.raise_for_status()
        data = resp.json()
        text = data["candidates"][0]["content"]["parts"][0]["text"]
    
    else:
        # Default: try OpenAI-compatible
        headers["Authorization"] = f"Bearer {api_key}"
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": temperature,
        }
        if response_json:
            payload["response_format"] = {"type": "json_object"}
        resp = requests.post(f"{base_url}/chat/completions", headers=headers, json=payload, timeout=120)
        resp.raise_for_status()
        data = resp.json()
        text = data["choices"][0]["message"]["content"]
    
    # Clean up response
    if text.startswith("```json"):
        text = text[7:]
    if text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    
    if response_json:
        return json.loads(text.strip())
    return text

def generate_report_sections(experiment_name: str, research_context: str) -> Dict[str, Any]:
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
    
    return call_llm(system_prompt, user_prompt, response_json=True)

def generate_circuit_design(experiment_name: str, connection_prompt: str) -> Dict[str, Any]:
    system_prompt = """You are an expert EEE circuit designer. Output valid JSON only."""
    
    user_prompt = f"""
Experiment: {experiment_name}
Connection Instructions: {connection_prompt if connection_prompt else "Design a standard, typical circuit for this experiment."}

Provide a JSON representation of the circuit:
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
Ensure the schemdraw_code contains a single function named draw_circuit(output_path).
"""
    
    return call_llm(system_prompt, user_prompt, response_json=True)