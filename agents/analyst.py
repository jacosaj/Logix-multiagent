"""
Data Analyst Agent - analizuje dane i tworzy wnioski
"""
from typing import Dict, Any
from datetime import datetime
import json
from langchain_core.messages import AIMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI

from .state import AgentState


class DataAnalystAgent:
    """Agent analityka danych"""
    
    def __init__(self, llm: ChatOpenAI):
        self.llm = llm
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """Jesteś Data Analyst. Analizujesz dane i tworzysz wnioski.
            
            Twoje zadania:
            - Analizować dane z SQL
            - Tworzyć statystyki i trendy
            - Identyfikować wzorce i anomalie
            - Formułować wnioski
            
            Dane SQL: {sql_results}
            
            Po analizie przekaż wyniki do Report Writer.
            """),
            MessagesPlaceholder(variable_name="messages")
        ])
        
        self.chain = self.prompt | self.llm
    
    def process(self, state: AgentState) -> Dict[str, Any]:
        """Przeanalizuj dane"""
        sql_results = state.get("sql_results", [])
        
        if not sql_results:
            return {
                "messages": [AIMessage(content="Brak danych do analizy. Przekazuję do SQL agenta.")],
                "next_agent": "sql_agent"
            }
        
        # Przeanalizuj dane
        response = self.chain.invoke({
            "messages": state["messages"],
            "sql_results": json.dumps(sql_results, indent=2, ensure_ascii=False)
        })
        
        # Zapisz wyniki analizy
        analysis_results = {
            "analysis": response.content,
            "timestamp": datetime.now().isoformat(),
            "data_points": len(sql_results)
        }
        
        return {
            "messages": [response],
            "analysis_results": analysis_results,
            "next_agent": "report_writer",
            "current_agent": "analyst"
        }