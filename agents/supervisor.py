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
            ("system", """Jesteś supervisorem zarządzającym zespołem agentów:
            - SQL Agent: odpytuje bazę danych, pobiera dane
            - Data Analyst: analizuje dane, tworzy statystyki i wnioski
            - Report Writer: tworzy raporty i podsumowania
            
            Twoim zadaniem jest:
            1. Zrozumieć zadanie użytkownika
            2. Zdecydować który agent powinien je wykonać
            3. Monitorować postęp i przekazywać zadania między agentami
            
            Obecny kontekst: {context}
            """),
            MessagesPlaceholder(variable_name="messages"),
            ("human", "Do którego agenta przekazać to zadanie?")
        ])
        
        self.chain = self.prompt | self.llm
    
    def process(self, state: AgentState) -> Dict[str, Any]:
        """Przetwórz stan i zdecyduj o następnym agencie"""
        # Przeanalizuj wiadomości i kontekst
        response = self.chain.invoke({
            "messages": state["messages"],
            "context": state.get("context", {})
        })
        
        # Określ następnego agenta na podstawie odpowiedzi
        content = response.content.lower()
        
        if "sql" in content or "dane" in content or "baz" in content:
            next_agent = "sql_agent"
        elif "analiz" in content or "statyst" in content:
            next_agent = "analyst"
        elif "raport" in content or "podsumow" in content:
            next_agent = "report_writer"
        else:
            next_agent = "end"
        
        return {
            "messages": [response],
            "next_agent": next_agent,
            "current_agent": "supervisor"
        }