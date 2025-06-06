"""
Builder grafu przepływu między agentami
"""
from typing import Dict, Any
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI

from agents import (
    AgentState,
    SupervisorAgent,
    SQLAgentNode,
    DataAnalystAgent,
    ReportWriterAgent
)
from config.settings import Config


class GraphBuilder:
    """Builder grafu przepływu między agentami"""
    
    def __init__(self, llm: ChatOpenAI, sql_agent_node: SQLAgentNode):
        self.llm = llm
        self.sql_agent_node = sql_agent_node
        
        # Inicjalizuj agentów
        self.supervisor = SupervisorAgent(llm)
        self.analyst = DataAnalystAgent(llm)
        self.report_writer = ReportWriterAgent(llm)
    
    def _route_next_agent(self, state: AgentState) -> str:
        """Określ następnego agenta na podstawie stanu"""
        next_agent = state.get("next_agent", "end")
        
        if next_agent == "end":
            return END
        
        return next_agent
    
    def build(self) -> StateGraph:
        """Zbuduj graf przepływu"""
        # Inicjalizuj graf
        workflow = StateGraph(AgentState)
        
        # Dodaj węzły
        workflow.add_node("supervisor", self.supervisor.process)
        workflow.add_node("sql_agent", self.sql_agent_node.process)
        workflow.add_node("analyst", self.analyst.process)
        workflow.add_node("report_writer", self.report_writer.process)
        
        # Ustaw punkt wejścia
        workflow.set_entry_point("supervisor")
        
        # Dodaj krawędzie warunkowe
        workflow.add_conditional_edges(
            "supervisor",
            self._route_next_agent,
            {
                "sql_agent": "sql_agent",
                "analyst": "analyst",
                "report_writer": "report_writer",
                END: END
            }
        )
        
        workflow.add_conditional_edges(
            "sql_agent",
            self._route_next_agent,
            {
                "supervisor": "supervisor",
                "analyst": "analyst",
                "report_writer": "report_writer",
                END: END
            }
        )
        
        workflow.add_conditional_edges(
            "analyst",
            self._route_next_agent,
            {
                "supervisor": "supervisor",
                "sql_agent": "sql_agent",
                "report_writer": "report_writer",
                END: END
            }
        )
        
        workflow.add_conditional_edges(
            "report_writer",
            self._route_next_agent,
            {
                "supervisor": "supervisor",
                END: END
            }
        )
        
        # Kompiluj graf
        return workflow.compile()
