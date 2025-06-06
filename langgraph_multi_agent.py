"""
Multi-Agent System z LangGraph - główny moduł
"""
from typing import Dict, Any, List
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI

from agents import AgentState, SQLAgentNode
from core.graph_builder import GraphBuilder
from config.settings import Config
from utils.conversation import ConversationHistory


class MultiAgentSystem:
    """System multi-agentowy z LangGraph"""
    
    def __init__(self, openai_api_key: str = None):
        self.api_key = openai_api_key or Config.OPENAI_API_KEY
        
        # Inicjalizuj LLM
        self.llm = ChatOpenAI(
            model=Config.OPENAI_MODEL,
            temperature=Config.TEMPERATURE,
            openai_api_key=self.api_key
        )
        
        # Inicjalizuj SQL agenta
        self.sql_agent_node = SQLAgentNode(self.api_key)
        
        # Zbuduj graf
        builder = GraphBuilder(self.llm, self.sql_agent_node)
        self.graph = builder.build()
        
        # Inicjalizuj historię konwersacji
        self.conversation_history = ConversationHistory()
    
    def process(self, user_input: str) -> Dict[str, Any]:
        """Przetwórz zapytanie użytkownika przez system multi-agentowy"""
        # Przygotuj stan początkowy
        initial_state = {
            "messages": [HumanMessage(content=user_input)],
            "current_agent": "supervisor",
            "context": {},
            "sql_results": [],
            "analysis_results": {},
            "next_agent": ""
        }
        
        # Uruchom graf
        result = self.graph.invoke(initial_state)
        
        return result
    
    def get_conversation_history(self, result: Dict[str, Any]) -> List[Dict[str, str]]:
        """Pobierz historię konwersacji w czytelnej formie"""
        return self.conversation_history.parse_result(result)
    
    def get_database_stats(self) -> Dict[str, Any]:
        """Pobierz statystyki bazy danych"""
        return self.sql_agent_node.get_database_stats()


# Przykład użycia
if __name__ == "__main__":
    # Utwórz system
    system = MultiAgentSystem()
    
    # Przykładowe zapytania
    queries = [
        "Pokaż mi analizę aktywności użytkowników w ostatnim tygodniu",
        "Który użytkownik spędził najwięcej czasu na social media?",
        "Stwórz raport o wykorzystaniu aplikacji biznesowych"
    ]
    
    for query in queries:
        print(f"\n{'='*60}")
        print(f"Pytanie: {query}")
        print(f"{'='*60}\n")
        
        result = system.process(query)
        
        # Wyświetl historię
        history = system.get_conversation_history(result)
        for entry in history:
            print(f"[{entry['role'].upper()}]: {entry['content']}")
            print("-" * 40)