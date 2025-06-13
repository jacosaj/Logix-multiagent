"""
Narzędzia do obsługi historii konwersacji
"""
from typing import Dict, Any, List
from langchain_core.messages import HumanMessage, AIMessage


class ConversationHistory:
    """Klasa do zarządzania historią konwersacji"""
    
    @staticmethod
    def parse_result(result: Dict[str, Any]) -> List[Dict[str, str]]:
        """
        Parsuj wynik z grafu do czytelnej historii konwersacji
        
        Args:
            result: Wynik z grafu LangGraph
            
        Returns:
            Lista wpisów historii konwersacji
        """
        history = []
        
        for msg in result.get("messages", []):
            if isinstance(msg, HumanMessage):
                history.append({
                    "role": "user",
                    "content": msg.content
                })
            elif isinstance(msg, AIMessage):
                # Określ który agent na podstawie treści
                agent = ConversationHistory._identify_agent(msg.content)
                
                history.append({
                    "role": agent,
                    "content": msg.content
                })
        
        return history
    
    @staticmethod
    def _identify_agent(content: str) -> str:
        """
        Identyfikuj agenta na podstawie treści wiadomości
        
        Args:
            content: Treść wiadomości
            
        Returns:
            Identyfikator agenta
        """
        content_lower = content.lower()
        
        # 1. Sprawdź explicit marker w treści
        if "[SQL_AGENT]" in content or "SQL Agent" in content:
            return "supervisor"
        elif "[DATA_ANALYST]" in content or content.startswith("📊 **Analiza danych zakończona**"):
            return "analyst"  
        elif "[REPORT_WRITER]" in content or "# 📊 Raport Analizy Danych" in content:
            return "report_writer"
        elif "[SUPERVISOR]" or "#Supervisor Agent" in content:
            return "sql_agent"
        
        # 2. Fallback - sprawdź current_agent ze stanu
        # (przekazywany z context)
        return "assistant"  # Domyślnie
    
    @staticmethod
    def format_for_display(history: List[Dict[str, str]]) -> str:
        """
        Formatuj historię do wyświetlenia
        
        Args:
            history: Lista wpisów historii
            
        Returns:
            Sformatowana historia jako string
        """
        formatted = []
        
        for entry in history:
            role = entry['role'].upper()
            content = entry['content']
            formatted.append(f"[{role}]: {content}")
        
        return "\n\n".join(formatted)
