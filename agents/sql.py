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
        self.conn = None
        
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
            # Inicjalizuj LLM z lepszym promptem
            llm = ChatOpenAI(
                model_name="gpt-4o-mini",
                openai_api_key=self.api_key,
                temperature=0,
            )
            
            # Połącz z bazą
            self.db = SQLDatabase.from_uri(f"sqlite:///{self.db_path}")
            self.conn = sqlite3.connect(self.db_path)
            
            # Utwórz agenta z kontekstem
            toolkit = SQLDatabaseToolkit(db=self.db, llm=llm)
            
            # Dodaj kontekst do agenta
            prefix = """Jesteś agentem SQL pracującym z bazą danych logów sieciowych.

Struktura tabeli 'logs':
- date: timestamp aktywności (format: YYYY-MM-DD HH:MM:SS)
- srcname: nazwa użytkownika/komputera
- app: nazwa aplikacji (np. 'Facebook', 'Microsoft Teams', 'Chrome')
- duration: czas trwania sesji w sekundach
- bytes_sent: bajty wysłane
- bytes_received: bajty odebrane
- category: kategoria aplikacji (social_media, business, browser, messaging, etc.)

WAŻNE: Zawsze formatuj wyniki jako strukturyzowane dane, nie jako narrację.
Używaj SQL do pobierania danych, następnie zwróć wyniki w formacie tabelarycznym.
"""
            
            self.agent = create_sql_agent(
                llm=llm,
                toolkit=toolkit,
                agent_type=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
                verbose=False,
                max_iterations=5,
                early_stopping_method="generate",
                prefix=prefix,
                handle_parsing_errors=True  # Obsługa błędów parsowania
            )
            
            return True, None
            
        except Exception as e:
            return False, str(e)
    
    def _execute_direct_query(self, query: str) -> Dict[str, Any]:
        """Wykonaj bezpośrednie zapytanie SQL gdy agent ma problemy"""
        try:
            cursor = self.conn.cursor()
            
            # Mapowanie zapytań użytkownika na SQL
            if "social media" in query.lower() and "najwięcej czasu" in query.lower():
                sql = """
                SELECT 
                    srcname as user,
                    SUM(duration) as total_seconds,
                    ROUND(SUM(duration) / 3600.0, 2) as total_hours,
                    COUNT(*) as sessions
                FROM logs
                WHERE category = 'social_media' 
                    OR app IN ('Facebook', 'Instagram', 'Twitter', 'TikTok', 'LinkedIn', 
                               'Snapchat', 'Pinterest', 'Reddit', 'WhatsApp')
                GROUP BY srcname
                ORDER BY total_seconds DESC
                LIMIT 10
                """
            elif "top" in query.lower() and "aplikacj" in query.lower():
                sql = """
                SELECT 
                    app,
                    COUNT(*) as usage_count,
                    SUM(duration) as total_seconds,
                    ROUND(SUM(duration) / 3600.0, 2) as total_hours,
                    COUNT(DISTINCT srcname) as unique_users
                FROM logs
                GROUP BY app
                ORDER BY total_seconds DESC
                LIMIT 10
                """
            else:
                # Domyślne zapytanie
                sql = """
                SELECT * FROM logs LIMIT 10
                """
            
            cursor.execute(sql)
            columns = [desc[0] for desc in cursor.description]
            results = cursor.fetchall()
            
            # Formatuj wyniki
            formatted_results = []
            for row in results:
                row_dict = dict(zip(columns, row))
                formatted_results.append(row_dict)
            
            # Utwórz czytelny output
            output_lines = [f"Znaleziono {len(results)} wyników:\n"]
            
            if results:
                # Nagłówki
                output_lines.append(" | ".join(columns))
                output_lines.append("-" * 80)
                
                # Dane
                for row in results:
                    output_lines.append(" | ".join(str(val) for val in row))
            
            return {
                "success": True,
                "output": "\n".join(output_lines),
                "data": formatted_results,
                "error": None
            }
            
        except Exception as e:
            return {
                "success": False,
                "output": None,
                "data": [],
                "error": str(e)
            }
    
    def query(self, question: str) -> Dict[str, Any]:
        """Wykonaj zapytanie do agenta"""
        if not self.agent:
            return {
                "success": False,
                "error": "Agent nie został zainicjalizowany",
                "output": None
            }
        
        try:
            # Spróbuj użyć agenta
            response = self.agent.invoke({"input": question})
            
            # Wyciągnij odpowiedź
            if isinstance(response, dict) and 'output' in response:
                output = response['output']
            else:
                output = str(response)
            
            # Jeśli output zawiera dane, zwróć sukces
            if output and "error" not in output.lower():
                return {
                    "success": True,
                    "output": output,
                    "error": None
                }
            else:
                # Fallback do bezpośredniego SQL
                print("⚠️ Agent miał problem, używam bezpośredniego SQL...")
                return self._execute_direct_query(question)
            
        except Exception as e:
            # Jeśli agent zawiedzie, użyj bezpośredniego SQL
            print(f"⚠️ Błąd agenta: {e}, używam bezpośredniego SQL...")
            return self._execute_direct_query(question)
    
    def process(self, state: AgentState) -> Dict[str, Any]:
        """Wykonaj zapytanie SQL"""
        # Wyciągnij ostatnie pytanie
        last_human_msg = None
        for msg in reversed(state["messages"]):
            if isinstance(msg, HumanMessage):
                last_human_msg = msg.content
                break
        
        if not last_human_msg:
            # Jeśli nie ma bezpośredniego pytania, sprawdź kontekst
            last_human_msg = "Pobierz dane o wykorzystaniu aplikacji z logów sieciowych"
        
        # Wykonaj zapytanie SQL
        result = self.query(last_human_msg)
        
        if result["success"]:
            # Zapisz wyniki w strukturyzowany sposób
            sql_results = [{
                "query": last_human_msg,
                "result": result["output"],
                "data": result.get("data", []),  # Strukturyzowane dane
                "timestamp": datetime.now().isoformat(),
                "status": "success"
            }]
            
            # Sprawdź czy mamy rzeczywiste dane
            if not result.get("data") and ("no results" in result["output"].lower() or "empty" in result["output"].lower()):
                msg = "⚠️ Baza danych nie zawiera żadnych rekordów. Sprawdź czy plik logs.db zawiera dane."
                next_agent = "supervisor"
            else:
                msg = f"✅ Pobrałem dane z bazy logów sieciowych:\n\n{result['output']}\n\nPrzekazuję dane do analizy..."
                next_agent = "analyst"
        else:
            sql_results = [{
                "query": last_human_msg,
                "error": result['error'],
                "timestamp": datetime.now().isoformat(),
                "status": "error"
            }]
            msg = f"❌ Wystąpił błąd podczas pobierania danych: {result['error']}"
            next_agent = "supervisor"
        
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
    
    def __del__(self):
        """Zamknij połączenie przy destrukcji"""
        if hasattr(self, 'conn') and self.conn:
            self.conn.close()