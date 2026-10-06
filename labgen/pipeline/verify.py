import json
import os
from pipeline.validators import text, data, structure, circuit, references, semantics

def run_all_checks(report):
    print("Running Verification Pipeline...")
    issues = []
    
    issues.extend(text.check_text(report))
    issues.extend(data.check_data(report))
    issues.extend(structure.check_structure(report))
    issues.extend(circuit.check_circuit(report))
    issues.extend(references.check_references(report))
    issues.extend(semantics.check_semantics(report))
    
    passed = len(issues) == 0
    warnings = len([i for i in issues if i.get("severity") == "medium"])
    failures = len([i for i in issues if i.get("severity") == "high"])
    
    result = {
        "summary": {"passed": passed, "warnings": warnings, "failures": failures},
        "issues": issues
    }
    return result

def write_report(results, path):
    with open(path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"Verification report written to {path}")
