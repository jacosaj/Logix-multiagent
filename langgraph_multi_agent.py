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
        
        # Ustaw konfigurację rekurencji
        self.config = {
            "recursion_limit": Config.MAX_ITERATIONS * 2,  # Podwójny limit dla bezpieczeństwa
            "max_concurrency": 1  # Sekwencyjne wykonanie
        }
        
        # Inicjalizuj historię konwersacji
        self.conversation_history = ConversationHistory()
    
    def process(self, user_input: str) -> Dict[str, Any]:
        """Przetwórz zapytanie użytkownika przez system multi-agentowy"""
        try:
            # Przygotuj stan początkowy
            initial_state = {
                "messages": [HumanMessage(content=user_input)],
                "current_agent": "supervisor",
                "context": {},
                "sql_results": [],
                "analysis_results": {},
                "next_agent": "",
                "iteration": 0  # Dodaj licznik iteracji
            }
            
            # Uruchom graf z konfiguracją
            print(f"🚀 Rozpoczynam przetwarzanie: {user_input}")
            
            # Użyj invoke z konfiguracją
            result = self.graph.invoke(
                initial_state,
                config=self.config
            )
            
            print("✅ Przetwarzanie zakończone")
            
            # Sprawdź czy otrzymaliśmy wynik
            if not result:
                print("⚠️ Brak wyniku z grafu")
                result = {
                    "messages": [HumanMessage(content="Przepraszam, wystąpił problem podczas przetwarzania zapytania.")],
                    "error": "Brak wyniku"
                }
            
            return result
            
        except Exception as e:
            print(f"❌ Błąd podczas przetwarzania: {str(e)}")
            
            # Zwróć błąd w strukturyzowany sposób
            error_message = f"Wystąpił błąd: {str(e)}"
            
            if "recursion" in str(e).lower():
                error_message = """Przepraszam, wystąpił problem z przetwarzaniem zapytania (przekroczono limit iteracji).
                
Możliwe przyczyny:
1. System zapętlił się między agentami
2. Brak danych w bazie
3. Problem z konfiguracją

Spróbuj ponownie lub sprawdź diagnostykę systemu."""
            
            return {
                "messages": [HumanMessage(content=error_message)],
                "error": str(e),
                "current_agent": "error",
                "sql_results": [],
                "analysis_results": {}
            }
    
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
    
    # Sprawdź stan bazy
    print("\n📊 Stan bazy danych:")
    db_stats = system.get_database_stats()
    for key, value in db_stats.items():
        print(f"  {key}: {value}")
    
    # Przykładowe zapytania
    queries = [
        "Stwórz raport o wykorzystaniu aplikacji - TOP 10 aplikacji",
        "Który użytkownik spędził najwięcej czasu na social media?",
    ]
    
    for query in queries:
        print(f"\n{'='*60}")
        print(f"Pytanie: {query}")
        print(f"{'='*60}\n")
        
        result = system.process(query)
        
        # Wyświetl historię
        history = system.get_conversation_history(result)
        for entry in history:
            print(f"[{entry['role'].upper()}]: {entry['content'][:200]}...")
            print("-" * 40)