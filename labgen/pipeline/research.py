import subprocess
import json
import os

KNOWLEDGE_HUB_PATH = "/home/sword/Documents/projects/tools/knowledge_hub.py"

def get_research_context(query):
    """
    Calls the external knowledge_hub.py script to perform a web search and
    returns a formatted string of the research context.
    """
    if not os.path.exists(KNOWLEDGE_HUB_PATH):
        print(f"Warning: knowledge_hub.py not found at {KNOWLEDGE_HUB_PATH}. Using internal DDGS fallback.")
        try:
            from duckduckgo_search import DDGS
            results = DDGS().text(query, max_results=5)
            context_lines = []
            for i, item in enumerate(results):
                title = item.get("title", "No Title")
                href = item.get("href", "No URL")
                body = item.get("body", "No Body")
                context_lines.append(f"[{i+1}] {title}\\nURL: {href}\\nSnippet: {body}\\n")
            return "\\n".join(context_lines)
        except ImportError:
            print("Please install duckduckgo-search (pip install duckduckgo-search) for internal research fallback.")
            return "No research context available."
    
    try:
        # knowledge_hub.py outputs JSON when called with --search
        result = subprocess.run(
            ["python", KNOWLEDGE_HUB_PATH, "--search", query],
            capture_output=True,
            text=True,
            check=True
        )
        
        data = json.loads(result.stdout)
        
        context_lines = []
        for i, item in enumerate(data):
            title = item.get("title", "No Title")
            href = item.get("href", "No URL")
            body = item.get("body", "No Body")
            context_lines.append(f"[{i+1}] {title}\\nURL: {href}\\nSnippet: {body}\\n")
            
        return "\\n".join(context_lines)
        
    except subprocess.CalledProcessError as e:
        print(f"Error calling knowledge_hub.py: {e.stderr}")
        return "Error retrieving research context."
    except json.JSONDecodeError as e:
        print(f"Error parsing knowledge_hub.py output: {e}")
        return "Error parsing research context."
    except Exception as e:
        print(f"Unexpected error in get_research_context: {e}")
        return "Error retrieving research context."
