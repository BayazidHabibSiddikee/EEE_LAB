import json
import os
from pathlib import Path

def get_settings_path():
    # Attempt to find settings.json in the project root
    current_dir = Path(__file__).parent.parent
    return current_dir / "settings.json"

def load_settings():
    settings_path = get_settings_path()
    if settings_path.exists():
        with open(settings_path) as f:
            return json.load(f)
    return {}

def save_settings(settings):
    settings_path = get_settings_path()
    with open(settings_path, "w") as f:
        json.dump(settings, f, indent=2)

def get_api_key():
    settings = load_settings()
    api_key = settings.get("api_key")
    if not api_key:
        api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        api_key = os.environ.get("LABGEN_API_KEY")
    return api_key
