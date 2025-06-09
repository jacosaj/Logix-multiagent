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
        
        # Licznik iteracji dla zabezpieczenia
        self.iteration_count = 0
        self.max_iterations = Config.MAX_ITERATIONS or 20  # Domyślnie 20 jeśli nie ustawiono
    
    def _route_next_agent(self, state: AgentState) -> str:
        """Określ następnego agenta na podstawie stanu"""
        # Zwiększ licznik iteracji
        self.iteration_count += 1
        
        # Zabezpieczenie przed nieskończoną pętlą
        if self.iteration_count >= self.max_iterations:
            print(f"⚠️ Osiągnięto limit iteracji ({self.max_iterations})")
            return END
        
        next_agent = state.get("next_agent", "end")
        
        # Debugowanie
        print(f"🔄 Routing: current_agent={state.get('current_agent')} -> next_agent={next_agent}")
        
        # Sprawdź warunki końcowe
        if next_agent == "end" or next_agent == END:
            print("✅ Kończę przepływ")
            return END
        
        # Dodatkowe zabezpieczenie - jeśli mamy kompletny raport, zakończ
        if state.get("current_agent") == "report_writer" and len(state.get("messages", [])) > 0:
            last_message = state["messages"][-1]
            if hasattr(last_message, 'content') and ("Raport końcowy" in last_message.content or "Raport o wykorzystaniu" in last_message.content):
                print("✅ Raport ukończony - kończę przepływ")
                return END
        
        return next_agent
    
    def build(self) -> StateGraph:
        """Zbuduj graf przepływu"""
        # Reset licznika przy każdym buildzie
        self.iteration_count = 0
        
        # Inicjalizuj graf
        workflow = StateGraph(AgentState)
        
        # Wrapper dla agentów z licznikiem iteracji
        def wrap_agent(agent_func):
            def wrapped(state):
                # Dodaj numer iteracji do stanu
                state["iteration"] = self.iteration_count
                return agent_func(state)
            return wrapped
        
        # Dodaj węzły z wrapperami
        workflow.add_node("supervisor", wrap_agent(self.supervisor.process))
        workflow.add_node("sql_agent", wrap_agent(self.sql_agent_node.process))
        workflow.add_node("analyst", wrap_agent(self.analyst.process))
        workflow.add_node("report_writer", wrap_agent(self.report_writer.process))
        
        # Ustaw punkt wejścia
        workflow.set_entry_point("supervisor")
        
        # Dodaj krawędzie warunkowe z uproszczoną logiką
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
                "report_writer": "report_writer",  # Usunięto sql_agent aby uniknąć zapętlenia
                END: END
            }
        )
        
        # Report writer może tylko zakończyć lub wrócić do supervisora
        workflow.add_conditional_edges(
            "report_writer",
            self._route_next_agent,
            {
                "supervisor": "supervisor",
                END: END
            }
        )
        
        # Kompiluj graf z ustawieniami
        compiled = workflow.compile()
        
        # Ustaw limit rekurencji
        compiled.recursion_limit = self.max_iterations * 2  # Podwójny limit dla bezpieczeństwa
        
        return compiled