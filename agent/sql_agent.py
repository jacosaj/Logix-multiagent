"""
SQL Agent - moduł zawierający logikę agenta SQL
"""
import os
import sqlite3
import pandas as pd
from typing import Optional, Tuple, Dict, Any

from langchain_openai import ChatOpenAI
from langchain_community.utilities.sql_database import SQLDatabase
from langchain_community.agent_toolkits.sql.toolkit import SQLDatabaseToolkit
from langchain_community.agent_toolkits.sql.base import create_sql_agent
from langchain.agents.agent_types import AgentType


class SQLAgent:
    """Klasa zarządzająca agentem SQL"""
    
    def __init__(self, openai_api_key: str = None):
        """
        Inicjalizacja agenta SQL
        
        Args:
            openai_api_key: Klucz API OpenAI (opcjonalny, może być w zmiennych środowiskowych)
        """
        self.agent = None
        self.db_path = None
        self.db = None
        self.api_key = openai_api_key or os.environ.get('OPENAI_API_KEY_TEG')
        
        if not self.api_key:
            raise ValueError("Brak klucza API OpenAI. Ustaw OPENAI_API_KEY_TEG w zmiennych środowiskowych.")
    
    def find_or_create_database(self) -> Optional[str]:
        """
        Znajdź istniejącą bazę danych lub utwórz nową z pliku CSV
        
        Returns:
            Ścieżka do bazy danych lub None
        """
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
    
    def initialize(self) -> Tuple[bool, Optional[str]]:
        """
        Inicjalizuj agenta SQL
        
        Returns:
            (success, error_message)
        """
        # Znajdź lub utwórz bazę danych
        self.db_path = self.find_or_create_database()
        
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
        """
        Wykonaj zapytanie do agenta
        
        Args:
            question: Pytanie w języku naturalnym
            
        Returns:
            Słownik z odpowiedzią i ewentualnym błędem
        """
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
    
    def get_database_stats(self) -> Dict[str, Any]:
        """
        Pobierz statystyki bazy danych
        
        Returns:
            Słownik ze statystykami lub błędem
        """
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
    
    def get_table_info(self) -> Dict[str, Any]:
        """
        Pobierz informacje o strukturze tabeli
        
        Returns:
            Słownik z informacjami o tabeli
        """
        if not self.db_path:
            return {"error": "Baza danych nie jest załadowana"}
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Pobierz informacje o kolumnach
            cursor.execute("PRAGMA table_info(logs)")
            columns = cursor.fetchall()
            
            # Pobierz przykładowe dane
            cursor.execute("SELECT * FROM logs LIMIT 5")
            sample_data = cursor.fetchall()
            
            conn.close()
            
            return {
                'columns': columns,
                'sample_data': sample_data
            }
        except Exception as e:
            return {'error': str(e)}


# Funkcje pomocnicze dla kompatybilności wstecznej
def create_agent(api_key: str = None) -> SQLAgent:
    """Utwórz i zainicjalizuj agenta SQL"""
    agent = SQLAgent(api_key)
    success, error = agent.initialize()
    
    if not success:
        raise Exception(f"Nie udało się zainicjalizować agenta: {error}")
    
    return agent