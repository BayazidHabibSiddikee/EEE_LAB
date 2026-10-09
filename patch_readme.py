import sys

with open("README.md", "r") as f:
    content = f.read()

cyberdeck_section = """
## 🖥️ Cyberdeck GUI (Web & Tauri Desktop)

LabGen now includes a fully responsive, highly accessible, and secure "Cyberdeck" UI built with React, Tailwind CSS, FastAPI, and Tauri.

### Run the Backend (FastAPI + WebSockets)
```bash
cd labgen
python backend/server.py
# Runs on http://localhost:8000
```

### Run the Frontend (Web)
```bash
cd labgen/frontend
npm install
npm run dev
# Runs on http://localhost:5173
```

### Run the Desktop App (Tauri)
```bash
cd labgen/frontend
npm run tauri dev
```

### UI Features
- **Cyberdeck Aesthetic:** Custom Tailwind theme with a clean, professional dark mode UI.
- **Accessibility (WCAG Compliant):** Full keyboard navigation support, visible focus rings, ARIA labels, semantic heading hierarchy, and `prefers-reduced-motion` respect.
- **Performance:** Virtualized terminal logs using `requestAnimationFrame`, debounced LocalStorage state, and minimal production bundles.
- **Security Hardened:** 
  - Strict Content Security Policy (CSP) in Tauri.
  - Safe shell execution constraints (restricted args).
  - API Key authentication and rate limiting on the FastAPI backend.
  - AST parsing for LLM-generated `schemdraw` code to prevent arbitrary execution.

"""

parts = content.split("## Features")
new_content = parts[0] + cyberdeck_section + "## Features" + parts[1]

with open("README.md", "w") as f:
    f.write(new_content)
