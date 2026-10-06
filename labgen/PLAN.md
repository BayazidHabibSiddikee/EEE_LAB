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
