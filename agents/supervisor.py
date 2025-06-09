"""
Supervisor Agent - zarządza przepływem zadań
"""
from typing import Dict, Any
from langchain_core.messages import AIMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI

from .state import AgentState


class SupervisorAgent:
    """Agent supervisora zarządzający przepływem zadań"""
    
    def __init__(self, llm: ChatOpenAI):
        self.llm = llm
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """Jesteś supervisorem zarządzającym zespołem agentów analizujących logi sieciowe.

KONTEKST BAZY DANYCH:
Pracujemy z bazą danych logów sieciowych zawierającą:
- date: data i czas aktywności
- srcname: nazwa użytkownika/komputera
- app: nazwa aplikacji (np. Facebook, Teams, Chrome, etc.)
- duration: czas trwania sesji
- bytes_sent/bytes_received: transfer danych
- category: kategoria aplikacji (social_media, business, browser, etc.)

TWOI AGENCI:
1. SQL Agent: ZAWSZE używaj go PIERWSZY gdy potrzebne są jakiekolwiek dane z bazy
2. Data Analyst: analizuje dane pobrane przez SQL Agent, tworzy statystyki
3. Report Writer: tworzy raporty TYLKO na podstawie danych z SQL i analizy

WAŻNE ZASADY:
- ZAWSZE rozpocznij od SQL Agent gdy użytkownik pyta o dane, raporty lub analizy
- NIGDY nie kieruj bezpośrednio do Report Writer bez wcześniejszego pobrania danych
- Dla zapytań o "raport", "analiza", "statystyki" - zawsze sekwencja: SQL → Analyst → Report Writer

Obecny kontekst: {context}
SQL Results dostępne: {has_sql_results}
"""),
            MessagesPlaceholder(variable_name="messages"),
            ("human", "Określ następnego agenta dla tego zadania.")
        ])
        
        self.chain = self.prompt | self.llm
    
    def process(self, state: AgentState) -> Dict[str, Any]:
        """Przetwórz stan i zdecyduj o następnym agencie"""
        # Sprawdź czy mamy już dane SQL
        has_sql_results = len(state.get("sql_results", [])) > 0
        
        # Przeanalizuj wiadomości i kontekst
        response = self.chain.invoke({
            "messages": state["messages"],
            "context": state.get("context", {}),
            "has_sql_results": has_sql_results
        })
        
        # Wyodrębnij ostatnie zapytanie użytkownika
        user_query = ""
        for msg in reversed(state["messages"]):
            if hasattr(msg, 'content') and msg.content and "User" not in str(type(msg)):
                user_query = msg.content.lower()
                break
        
        # Logika routingu
        content = response.content.lower()
        
        # Jeśli pytanie dotyczy danych/raportów/analiz i nie mamy jeszcze danych SQL
        if not has_sql_results and any(keyword in user_query for keyword in 
            ["raport", "analiz", "statyst", "pokaż", "wykorzyst", "aktywn", "użytkown", "aplikacj"]):
            next_agent = "sql_agent"
            response_msg = "Rozumiem, że potrzebujesz raportu o wykorzystaniu aplikacji. Przekazuję zadanie do SQL Agent, aby pobrał odpowiednie dane z bazy logów sieciowych."
        
        # Jeśli mamy dane SQL ale nie analizę
        elif has_sql_results and not state.get("analysis_results"):
            next_agent = "analyst"
            response_msg = "Mamy już dane z bazy. Przekazuję je do Data Analyst do analizy."
        
        # Jeśli mamy dane i analizę
        elif has_sql_results and state.get("analysis_results"):
            next_agent = "report_writer"
            response_msg = "Dane zostały pobrane i przeanalizowane. Przekazuję do Report Writer do stworzenia raportu."
        
        # Jeśli Report Writer już stworzył raport - kończymy
        elif state.get("current_agent") == "report_writer":
            next_agent = "end"
            response_msg = "Raport został utworzony. Kończę przepływ."
        
        # Domyślnie - określ na podstawie treści
        else:
            if "sql" in content or "dane" in content or "baz" in content:
                next_agent = "sql_agent"
                response_msg = response.content
            elif "analiz" in content or "statyst" in content:
                next_agent = "analyst"
                response_msg = response.content
            elif "raport" in content or "podsumow" in content:
                # Jeśli nie ma danych, najpierw pobierz
                if not has_sql_results:
                    next_agent = "sql_agent"
                    response_msg = "Aby stworzyć raport, najpierw muszę pobrać dane. Przekazuję do SQL Agent."
                else:
                    next_agent = "report_writer"
                    response_msg = response.content
            else:
                next_agent = "end"
                response_msg = response.content
        
        return {
            "messages": [AIMessage(content=response_msg)],
            "next_agent": next_agent,
            "current_agent": "supervisor"
        }