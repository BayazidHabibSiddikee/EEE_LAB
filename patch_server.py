import re

with open("labgen/backend/server.py", "r") as f:
    content = f.read()

# Add global dicts
if "intervention_events = {}" not in content:
    content = content.replace("manager = ConnectionManager()", "manager = ConnectionManager()\nintervention_events = {}\nintervention_actions = {}")

# Fix msg.action error
old_intervention_ws = """                elif msg.type == "intervention_response":
                    # Handle intervention response - would need to communicate with running generation
                    # For now, just acknowledge
                    await websocket.send_text(json.dumps({
                        "type": "intervention_ack",
                        "reportId": msg.reportId,
                        "action": msg.action
                    }))"""

new_intervention_ws = """                elif msg.type == "intervention_response":
                    report_id = msg.reportId
                    action = msg_dict.get("action")
                    if report_id in intervention_events:
                        intervention_actions[report_id] = action
                        intervention_events[report_id].set()
                        
                    await websocket.send_text(json.dumps({
                        "type": "intervention_ack",
                        "reportId": report_id,
                        "action": action
                    }))"""

content = content.replace(old_intervention_ws, new_intervention_ws)

# Add logic inside run_generation_with_progress
loop_logic_old = """            else:
                # Generic progress for current stage
                if current_stage in stage_progress:
                    stage_progress[current_stage] = min(100, stage_progress[current_stage] + 2)
                    await emit_stage_event(websocket, report_id, "stage_progress", current_stage, {
                        "progress": stage_progress[current_stage],
                        "log": line_str
                    })
            
            # Also send raw log for terminal"""

loop_logic_new = """            elif "error" in line_lower and "validation error" not in line_lower:
                # Ask for intervention
                import signal
                
                try:
                    os.kill(process.pid, signal.SIGSTOP)
                except Exception:
                    pass
                
                event = asyncio.Event()
                intervention_events[report_id] = event
                
                await websocket.send_text(json.dumps({
                    "type": "intervention_required",
                    "reportId": report_id,
                    "stage": current_stage,
                    "message": line_str,
                    "params": {"process_pid": process.pid}
                }))
                
                await event.wait()
                action = intervention_actions.pop(report_id, "retry")
                del intervention_events[report_id]
                
                if action == "abort":
                    try:
                        process.terminate()
                    except Exception:
                        pass
                    break
                else:
                    try:
                        os.kill(process.pid, signal.SIGCONT)
                    except Exception:
                        pass
            else:
                # Generic progress for current stage
                if current_stage in stage_progress:
                    stage_progress[current_stage] = min(100, stage_progress[current_stage] + 2)
                    await emit_stage_event(websocket, report_id, "stage_progress", current_stage, {
                        "progress": stage_progress[current_stage],
                        "log": line_str
                    })
            
            # Also send raw log for terminal"""

content = content.replace(loop_logic_old, loop_logic_new)

with open("labgen/backend/server.py", "w") as f:
    f.write(content)
