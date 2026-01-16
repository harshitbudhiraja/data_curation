"""LangGraph state definition for data_curation."""
from typing import TypedDict, Annotated, Sequence, Optional
from langchain_core.messages import BaseMessage
import operator


class AgentState(TypedDict):
    """State shared between student and tutor agents.
    
    Attributes:
        messages: Conversation history (accumulated)
        problem_text: Initial problem statement
        test_cases: List of test assertions
        personality_prompt: Student personality prompt text
        turn_count: Number of conversation turns
        max_turns: Maximum allowed turns before termination
        execution_result: Result from code execution
        solved: Whether the problem has been solved
        execution_history: List of all execution results per turn
    """
    messages: Annotated[Sequence[BaseMessage], operator.add]
    problem_text: str
    test_cases: list
    personality_prompt: str
    personality: str
    turn_count: int
    max_turns: int
    execution_result: Optional[dict]
    solved: bool
    execution_history: list
