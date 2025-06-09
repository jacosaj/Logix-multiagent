"""
Report Writer Agent - tworzy profesjonalne raporty
"""
from typing import Dict, Any
from datetime import datetime
import json
from langchain_core.messages import AIMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI

from .state import AgentState


class ReportWriterAgent:
    """Agent tworzący raporty"""
    
    def __init__(self, llm: ChatOpenAI):
        self.llm = llm
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """Jesteś Report Writer tworzącym profesjonalne raporty z analizy logów sieciowych.

WAŻNE ZASADY:
1. UŻYWAJ TYLKO rzeczywistych danych z SQL i analizy - NIGDY nie wymyślaj liczb!
2. Jeśli nie masz danych, zgłoś to wyraźnie
3. Formatuj raport profesjonalnie używając markdown
4. Zawrzyj konkretne liczby i procenty z otrzymanych danych

STRUKTURA RAPORTU:
1. Tytuł i data
2. Podsumowanie wykonawcze (executive summary)
3. Kluczowe wskaźniki (z rzeczywistymi danymi)
4. Szczegółowa analiza
5. Wnioski i rekomendacje
6. Metodologia (skąd pochodzą dane)

Dane SQL: {sql_results}
Wyniki analizy: {analysis_results}

Pamiętaj: Jeśli nie otrzymałeś danych z SQL lub analizy, NIE generuj fikcyjnych liczb!
"""),
            MessagesPlaceholder(variable_name="messages")
        ])
        
        self.chain = self.prompt | self.llm
    
    def process(self, state: AgentState) -> Dict[str, Any]:
        """Utwórz raport"""
        sql_results = state.get("sql_results", [])
        analysis_results = state.get("analysis_results", {})
        
        # Sprawdź czy mamy rzeczywiste dane
        has_real_data = (
            sql_results and 
            sql_results[0].get("status") == "success" and 
            analysis_results.get("status") == "success"
        )
        
        if not has_real_data:
            # Nie mamy danych - zgłoś problem
            error_report = f"""
# ⚠️ Raport o wykorzystaniu aplikacji

## Status: Brak danych

### Problem
Nie mogę utworzyć raportu, ponieważ nie otrzymałem rzeczywistych danych z bazy.

### Przyczyny:
{f"- Błąd SQL: {sql_results[0].get('error')}" if sql_results and sql_results[0].get("status") == "error" else ""}
{f"- Brak danych w bazie logów" if analysis_results.get("status") == "no_data" else ""}
{"- Brak wyników z SQL Agent" if not sql_results else ""}
{"- Brak analizy danych" if not analysis_results else ""}

### Rekomendacje:
1. Sprawdź czy plik `logs.db` zawiera dane
2. Upewnij się, że tabela `logs` istnieje i ma rekordy
3. Zweryfikuj strukturę tabeli (date, srcname, app, duration, etc.)

---
*Wygenerowano: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""
            return {
                "messages": [AIMessage(content=error_report)],
                "next_agent": "end",
                "current_agent": "report_writer"
            }
        
        # Mamy dane - utwórz prawdziwy raport
        response = self.chain.invoke({
            "messages": state["messages"],
            "sql_results": json.dumps(sql_results, indent=2, ensure_ascii=False),
            "analysis_results": json.dumps(analysis_results, indent=2, ensure_ascii=False)
        })
        
        # Dodaj stopkę z informacją o źródle danych
        final_report = f"""{response.content}

---
### 📊 Źródło danych
- Baza: `logs.db` (logi sieciowe)
- Liczba przeanalizowanych aplikacji: {analysis_results.get('data_summary', {}).get('apps_analyzed', 0)}
- Liczba użytkowników: {analysis_results.get('data_summary', {}).get('users_analyzed', 0)}
- Data analizy: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        
        return {
            "messages": [AIMessage(content=final_report)],
            "next_agent": "end",
            "current_agent": "report_writer"
        }