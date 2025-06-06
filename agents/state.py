"""
Stan współdzielony między agentami
"""
from typing import Dict, Any, List, TypedDict, Annotated
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


class AgentState(TypedDict):
    """Stan przekazywany między agentami"""
    messages: Annotated[List[BaseMessage], add_messages]
    current_agent: str
    context: Dict[str, Any]  # Kontekst współdzielony między agentami
    sql_results: List[Dict[str, Any]]  # Wyniki z SQL
    analysis_results: Dict[str, Any]  # Wyniki analizy
    next_agent: str  # Który agent ma przejąć