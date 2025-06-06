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
            ("system", """Jesteś Report Writer. Tworzysz profesjonalne raporty.
            
            Twoje zadania:
            - Tworzyć czytelne podsumowania
            - Formatować wyniki w przejrzysty sposób
            - Dodawać rekomendacje
            - Używać markdown dla lepszej czytelności
            
            Dane SQL: {sql_results}
            Analiza: {analysis_results}
            """),
            MessagesPlaceholder(variable_name="messages")
        ])
        
        self.chain = self.prompt | self.llm
    
    def process(self, state: AgentState) -> Dict[str, Any]:
        """Utwórz raport"""
        sql_results = state.get("sql_results", [])
        analysis_results = state.get("analysis_results", {})
        
        # Utwórz raport
        response = self.chain.invoke({
            "messages": state["messages"],
            "sql_results": json.dumps(sql_results, indent=2, ensure_ascii=False),
            "analysis_results": json.dumps(analysis_results, indent=2, ensure_ascii=False)
        })
        
        # Dodaj podsumowanie
        final_report = f"""
# 📊 Raport końcowy

{response.content}

---
*Raport wygenerowany: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""
        
        return {
            "messages": [AIMessage(content=final_report)],
            "next_agent": "end",
            "current_agent": "report_writer"
        }