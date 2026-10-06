# LabGen Architecture

The LabGen pipeline is built using a modern AI agent framework (LangGraph) integrated with traditional engineering simulation tools (`ngspice`).

## Core Components

1. **State Graph (LangGraph):**
   - The drafting process is modeled as a state machine. The state holds the `experiment_name`, `circuit_prompt`, `research_context`, `circuit_design`, and the final `report_sections`.
   - **Nodes:**
     - `research_node`: Gathers context using `knowledge_hub.py` or the `store/` PDF vector DB.
     - `circuit_node`: Designs the circuit (netlist + schemdraw python code) based on the prompt.
     - `drafting_node`: Writes the Introduction, Objectives, Discussion, and Conclusion.

2. **Simulation Engine (`simulate.py`):**
   - Takes the LLM-generated netlist.
   - Executes `ngspice` in batch mode.
   - Parses the output (`iv_data.txt`) into a Pandas DataFrame.
   - Plots waveforms using `matplotlib`.

3. **Assembly Engine (`assemble.py`):**
   - Merges the LLM JSON outputs, generated images, and simulation data.
   - Injects them into `templates/report.tex.j2`.
   - Compiles the final PDF using `tectonic`.
