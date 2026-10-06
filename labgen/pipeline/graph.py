from typing import TypedDict, Dict, Any
from langgraph.graph import StateGraph, START, END
from pipeline.llm import generate_circuit_design, generate_report_sections
from pipeline.research import get_research_context

class LabState(TypedDict):
    experiment_name: str
    circuit_prompt: str
    research_context: str
    circuit_json: Dict[str, Any]
    report_sections: Dict[str, Any]

def gather_research(state: LabState):
    print("Graph: Gathering research context...")
    context = get_research_context(state["experiment_name"])
    return {"research_context": context}

def design_circuit(state: LabState):
    print("Graph: Designing circuit...")
    circuit = generate_circuit_design(state["experiment_name"], state["circuit_prompt"])
    return {"circuit_json": circuit}

def draft_report(state: LabState):
    print("Graph: Drafting report sections...")
    sections = generate_report_sections(state["experiment_name"], state["research_context"])
    return {"report_sections": sections}

def build_graph():
    workflow = StateGraph(LabState)
    
    workflow.add_node("research", gather_research)
    workflow.add_node("circuit", design_circuit)
    workflow.add_node("draft", draft_report)
    
    workflow.add_edge(START, "research")
    workflow.add_edge(START, "circuit")
    workflow.add_edge("research", "draft")
    # drafting doesn't strictly depend on circuit in this simple version, but both go to END
    workflow.add_edge("circuit", END)
    workflow.add_edge("draft", END)
    
    return workflow.compile()

def run_pipeline(experiment_name: str, circuit_prompt: str):
    app = build_graph()
    initial_state = {
        "experiment_name": experiment_name,
        "circuit_prompt": circuit_prompt,
        "research_context": "",
        "circuit_json": {},
        "report_sections": {}
    }
    result = app.invoke(initial_state)
    return result
