# Development Plan

## Phase 1: Core Scaffolding (Completed)
- [x] Basic Python CLI.
- [x] LaTeX Jinja2 templates.
- [x] Ngspice integration.

## Phase 2: AI Integration (Completed)
- [x] Integrate Gemini API for drafting sections.
- [x] Dynamic circuit design prompt generation.
- [x] Fallback mechanisms for simulation.

## Phase 3: LangGraph & Architecture (Current)
- [x] Define LangGraph state schema.
- [x] Implement LangChain wrappers.
- [x] Centralize config in `settings.json`.
- [x] Ensure strict formatting (bordered tables, strict font sizes).

## Phase 4: Advanced RAG (Future)
- [ ] Implement OCR pipeline for documents in `store/`.
- [ ] Vector database integration (e.g., ChromaDB or FAISS).
- [ ] Advanced self-correction loops for `ngspice` convergence errors.

## Phase 5: Verification Pipeline (In Progress)
- [x] Scaffold `verify.py` and `validators/` directory.
- [ ] Implement Rule-based validators (`text.py`, `data.py`, `structure.py`, `circuit.py`).
- [ ] Implement LLM Semantic validator (`semantics.py`) for physics/logic checks.
- [ ] Build standalone CLI for verifying external PDF submissions.
- [ ] Train XGBoost/LightGBM classifier using weak supervision (Snorkel) on 200 unlabeled PDFs to act as a fast pre-filter.

## Phase 6: Open Source / Local AI Migration (Future)
- [ ] Transition FluidSim Linux clone into a native MCP server for PLC design.
- [ ] Fine-tune an open-source model (e.g., Qwen 2.5) for native tool-calling (ReAct/MCP) to replace Gemini.
- [ ] Create synthetic training datasets from verified-good LabGen runs to train the local model for end-to-end report generation.
