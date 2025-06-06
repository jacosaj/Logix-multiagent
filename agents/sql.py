"""
SQL Agent - wykonuje zapytania do bazy danych
"""
import os
import sqlite3
import pandas as pd
from typing import Dict, Any, Optional, Tuple
from datetime import datetime
from langchain_core.messages import AIMessage, HumanMessage

from langchain_openai import ChatOpenAI
from langchain_community.utilities.sql_database import SQLDatabase
from langchain_community.agent_toolkits.sql.toolkit import SQLDatabaseToolkit
from langchain_community.agent_toolkits.sql.base import create_sql_agent
from langchain.agents.agent_types import AgentType

from .state import AgentState


class SQLAgentNode:
    """Agent SQL wykonujący zapytania do bazy danych"""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.environ.get('OPENAI_API_KEY_TEG')
        self.agent = None
        self.db_path = None
        self.db = None
        
        # Inicjalizuj agenta
        success, error = self._initialize()
        if not success:
            raise Exception(f"Nie udało się zainicjalizować SQL agenta: {error}")
    
    def _find_or_create_database(self) -> Optional[str]:
        """Znajdź istniejącą bazę danych lub utwórz nową z pliku CSV"""
        # Możliwe lokalizacje bazy danych
        possible_db_paths = [
            "./logs.db",
            "./parser/logs.db", 
            "../parser/logs.db",
            "logs.db",
            "./data/logs.db"
        ]
        
        # Znajdź bazę danych
        for path in possible_db_paths:
            if os.path.exists(path):
                return path
        
        # Jeśli nie ma bazy, spróbuj utworzyć z CSV
        csv_files = [f for f in os.listdir('.') if 'logi' in f.lower() and f.endswith('.csv')]
        if csv_files:
            try:
                csv_file = csv_files[0]
                db_path = "logs.db"
                
                df = pd.read_csv(csv_file)
                conn = sqlite3.connect(db_path)
                df.to_sql('logs', conn, if_exists='replace', index=False)
                conn.close()
                
                print(f"✅ Utworzono bazę z pliku CSV: {csv_file}")
                return db_path
            except Exception as e:
                print(f"❌ Błąd tworzenia bazy: {e}")
                return None
        
        return None
    
    def _initialize(self) -> Tuple[bool, Optional[str]]:
        """Inicjalizuj agenta SQL"""
        # Znajdź lub utwórz bazę danych
        self.db_path = self._find_or_create_database()
        
        if not self.db_path:
            return False, "Nie znaleziono bazy danych ani plików CSV do jej utworzenia"
        
        try:
            # Inicjalizuj LLM
            llm = ChatOpenAI(
                model_name="gpt-4o-mini",
                openai_api_key=self.api_key,
                temperature=0,
            )
            
            # Połącz z bazą
            self.db = SQLDatabase.from_uri(f"sqlite:///{self.db_path}")
            
            # Utwórz agenta
            toolkit = SQLDatabaseToolkit(db=self.db, llm=llm)
            
            self.agent = create_sql_agent(
                llm=llm,
                toolkit=toolkit,
                agent_type=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
                verbose=False,
                max_iterations=10,
                early_stopping_method="generate"
            )
            
            return True, None
            
        except Exception as e:
            return False, str(e)
    
    def query(self, question: str) -> Dict[str, Any]:
        """Wykonaj zapytanie do agenta"""
        if not self.agent:
            return {
                "success": False,
                "error": "Agent nie został zainicjalizowany",
                "output": None
            }
        
        try:
            response = self.agent.invoke({"input": question})
            
            # Wyciągnij odpowiedź
            if isinstance(response, dict) and 'output' in response:
                output = response['output']
            else:
                output = str(response)
            
            return {
                "success": True,
                "output": output,
                "error": None
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "output": None
            }
    
    def process(self, state: AgentState) -> Dict[str, Any]:
        """Wykonaj zapytanie SQL"""
        # Wyciągnij ostatnie pytanie
        last_human_msg = None
        for msg in reversed(state["messages"]):
            if isinstance(msg, HumanMessage):
                last_human_msg = msg.content
                break
        
        if not last_human_msg:
            return {
                "messages": [AIMessage(content="Nie znalazłem pytania do wykonania")],
                "next_agent": "supervisor"
            }
        
        # Wykonaj zapytanie SQL
        result = self.query(last_human_msg)
        
        # Zapisz wyniki
        sql_results = state.get("sql_results", [])
        sql_results.append({
            "query": last_human_msg,
            "result": result["output"] if result["success"] else f"Błąd: {result['error']}",
            "timestamp": datetime.now().isoformat()
        })
        
        # Określ następnego agenta
        if result["success"] and ("analiz" in last_human_msg.lower() or "statyst" in last_human_msg.lower()):
            next_agent = "analyst"
            msg = f"Pobrałem dane z bazy:\n{result['output']}\n\nPrzekazuję do analizy..."
        elif result["success"]:
            next_agent = "report_writer"
            msg = f"Pobrałem dane z bazy:\n{result['output']}\n\nPrzekazuję do utworzenia raportu..."
        else:
            next_agent = "supervisor"
            msg = f"Wystąpił problem: {result['error']}"
        
        return {
            "messages": [AIMessage(content=msg)],
            "sql_results": sql_results,
            "next_agent": next_agent,
            "current_agent": "sql_agent"
        }
    
    def get_database_stats(self) -> Dict[str, Any]:
        """Pobierz statystyki bazy danych"""
        if not self.db_path:
            return {"error": "Baza danych nie jest załadowana"}
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Podstawowe statystyki
            cursor.execute("SELECT COUNT(*) FROM logs")
            total_rows = cursor.fetchone()[0]
            
            cursor.execute("SELECT MIN(date) as min_date, MAX(date) as max_date FROM logs")
            date_range = cursor.fetchone()
            
            cursor.execute("SELECT COUNT(DISTINCT srcname) FROM logs")
            unique_users = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(DISTINCT app) FROM logs")
            unique_apps = cursor.fetchone()[0]
            
            conn.close()
            
            return {
                'total_rows': total_rows,
                'date_range': date_range,
                'unique_users': unique_users,
                'unique_apps': unique_apps,
                'db_path': self.db_path
            }
        except Exception as e:
            return {'error': str(e)}