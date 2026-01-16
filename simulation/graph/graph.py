"""LangGraph assembly and compilation - adapted for data_curation."""
from langgraph.graph import StateGraph, END
from simulation.graph.state import AgentState
from simulation.graph.nodes import student_node, tutor_node, execution_node
from simulation.graph.router import route_next_agent, route_after_execution


def create_simulation_graph():
    """Create and compile the agent conversation graph with code execution.
    
    Flow:
    1. Student asks question
    2. Tutor provides code
    3. Execute code & check tests
    4. If solved -> END, else loop back to student
    
    Returns:
        Compiled LangGraph workflow
    """
    # Initialize graph with state schema
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("student", student_node)
    workflow.add_node("tutor", tutor_node)
    workflow.add_node("execute", execution_node)
    
    # Set entry point (student always starts)
    workflow.set_entry_point("student")
    
    # After student -> go to tutor
    workflow.add_edge("student", "tutor")
    
    # After tutor -> execute the code
    workflow.add_edge("tutor", "execute")
    
    # After execution -> check if solved
    workflow.add_conditional_edges(
        "execute",
        route_after_execution,
        {
            "continue": "student",  # Loop back to student
            "end": END  # Problem solved or max turns
        }
    )
    
    # Compile and return
    return workflow.compile()
