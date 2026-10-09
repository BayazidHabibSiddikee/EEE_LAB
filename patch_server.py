import re

with open('labgen/backend/server.py', 'r') as f:
    code = f.read()

replacement = """            # Heuristic progress updating
            line_lower = line_str.lower()
            if "rag" in line_lower: progress = min(30, progress + 5)
            elif "circuit" in line_lower: progress = min(50, progress + 5)
            elif "report" in line_lower: progress = min(70, progress + 5)
            elif "verification" in line_lower: progress = min(90, progress + 5)
"""

old_code = """            # Heuristic progress updating
            if "RAG" in line_str: progress = min(30, progress + 5)
            elif "Circuit" in line_str: progress = min(50, progress + 5)
            elif "Report" in line_str: progress = min(70, progress + 5)
            elif "verification" in line_str.lower(): progress = min(90, progress + 5)"""

code = code.replace(old_code, replacement)

# Define constants at top
constants = """
# Progress Stage Thresholds (max_progress, step_increment)
PROGRESS_STAGES = {
    "rag": (30, 5),
    "circuit": (50, 5),
    "report": (70, 5),
    "verification": (90, 5)
}
"""

if "PROGRESS_STAGES =" not in code:
    code = code.replace("import logging", "import logging\n" + constants)
    
new_replacement = """            # Heuristic progress updating
            line_lower = line_str.lower()
            for stage, (max_val, step) in PROGRESS_STAGES.items():
                if stage in line_lower:
                    progress = min(max_val, progress + step)
                    break
"""
code = code.replace(replacement, new_replacement)

with open('labgen/backend/server.py', 'w') as f:
    f.write(code)
