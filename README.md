# LabGen: EEE Laboratory Report Generator

LabGen is an automated pipeline for generating Electrical and Electronic Engineering (EEE) laboratory reports in PDF format. It uses LLMs for intelligent drafting, ngspice for circuit simulation, and LaTeX for high-quality PDF rendering.

## Features
- **Dynamic Circuit Generation:** Provide a natural language prompt, and the LLM designs the circuit, generates a netlist for `ngspice`, and draws the schematic using `schemdraw`.
- **RAG-Powered Research:** Integrates with an optional knowledge hub to retrieve factual data (datasheets, theories) using BM25 and web search.
- **LangGraph Architecture:** Uses LangGraph and LangChain for stateful, section-by-section drafting and verification.
- **Strict Formatting:** Adheres to the RUET standard (Times New Roman 12pt, bold headings, full-bordered tables).

## Setup
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Configure settings in `settings.json`:
   ```json
   {
     "llm": {
       "api_key": "YOUR_GEMINI_API_KEY",
       "model": "gemini-2.5-pro",
       "endpoint": "https://generativelanguage.googleapis.com/v1beta"
     },
     "scraper": {
       "enabled": true
     }
   }
   ```
   *Note: For the highly powerful automated image scraping feature (which grabs and crops reference diagrams), you need to have `camoufox` installed (`pip install camoufox`). If you do not have it, the pipeline will gracefully skip scraping. The built-in research uses `duckduckgo-search` by default.*

3. Run the pipeline:
   ```bash
   # Basic run
   python main.py "Study of Diode Characteristics"
   
   # With a specific circuit prompt
   python main.py "Study of Diode Characteristics" --circuit-prompt "A diode in series with a 1k resistor connected to a DC sweep voltage."
   ```

## Ecosystem & Folder Structure

To unlock the full potential of LabGen (including PLC circuit generation and automated reference image cropping), it is recommended to set up the ecosystem side-by-side with symbolic links:

```text
EEE_LAB/
├── labgen/                 # Your automated PDF pipeline (This repository)
├── web-scraper/            # Symlinked -> /path/to/web-scraper
└── FluidSim-Linux/         # Symlinked -> /path/to/FluidSim-Linux (Contains the MCP Server!)
```

### Optional but Powerful Extensions:
1. **[FluidSim-Linux](https://github.com/BayazidHabibSiddikee/FluidSim-Linux)**: A Python-based clone of FluidSim. Includes a native MCP server, allowing the LLM to dynamically design and render PLC, pneumatic, and hydraulic circuits directly into your reports.
2. **[Web-Scraper](https://github.com/BayazidHabibSiddikee/web-scraper)**: A highly powerful scraping suite powered by `camoufox`. Allows LabGen to automatically browse the web, screenshot reference diagrams (e.g., from datasheets or Wikipedia), crop them, and inject them into the Theory section.

### LabGen Internal Structure:
- `pipeline/`: Core logic (LLM, LangGraph, research, simulation).
- `store/`: Place reference PDFs here for the optional OCR/RAG system.
- `templates/`: Jinja2 templates for LaTeX generation.
- `settings.json`: User configuration (API keys, university data).
