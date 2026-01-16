"""Conditional routing logic for LangGraph - adapted for data_curation."""
from simulation.graph.state import AgentState


def should_continue(state: AgentState) -> str:
    """Determine if conversation should continue based on execution results.
    
    Logic:
    - If tests passed (solved=True), end conversation
    - Otherwise continue up to max_turns
    
    Returns:
        'continue' to keep going, 'end' to stop
    """
    # If problem is solved, end
    if state.get("solved", False):
        return "end"
    
    # Check max turns limit
    if state["turn_count"] >= state.get("max_turns", 15):
        return "end"
    
    # Otherwise continue
    return "continue"


def route_after_execution(state: AgentState) -> str:
    """Route after code execution.
    
    If tests pass, END immediately (don't go back to student).
    If tests fail, go back to student for correction.
    
    Args:
        state: Current graph state
    
    Returns:
        "continue" to go back to student, "end" to stop
    """
    # If problem is solved, END immediately
    if state.get("solved", False):
        return "end"
    
    # Check max turns limit
    if state["turn_count"] >= state.get("max_turns", 15):
        return "end"
    
    # Tests failed - go back to student for correction
    return "continue"


def route_next_agent(state: AgentState) -> str:
    """Determine which agent speaks next.
    
    Args:
        state: Current graph state
    
    Returns:
        "student", "tutor", or "execute"
    """
    messages = state["messages"]
    
    # Check max turns limit
    if state["turn_count"] >= state.get("max_turns", 15):
        return "end"
    
    # First turn - student starts
    if not messages or state["turn_count"] == 0:
        return "student"
    
    # Check last message's role
    last_message = messages[-1]
    last_agent = last_message.name if hasattr(last_message, 'name') else last_message.get('name')
    
    # After student speaks, tutor responds
    if last_agent == "student":
        return "tutor"
    
    # After tutor speaks with code, execute it
    if last_agent == "tutor":
        return "execute"
    
    # Default to student
    return "student"
