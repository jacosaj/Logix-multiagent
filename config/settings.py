"""
Konfiguracja systemu multi-agentowego
"""
import os
from dotenv import load_dotenv

# Załaduj zmienne środowiskowe
load_dotenv()


class Config:
    """Konfiguracja systemu"""
    
    # OpenAI
    OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY_TEG')
    OPENAI_MODEL = "gpt-4o-mini"
    TEMPERATURE = 0
    
    # Agent settings
    MAX_ITERATIONS = 20
    VERBOSE = True
    
    # Database paths
    DB_SEARCH_PATHS = [
        "./logs.db",
        "./parser/logs.db", 
        "../parser/logs.db",
        "logs.db",
        "./data/logs.db"
    ]
    
    # UI settings
    PAGE_TITLE = "🤖 Multi-Agent System - Analiza Logów Sieciowych"
    PAGE_ICON = "🤖"
    LAYOUT = "wide"
    
    # Agent emojis
    AGENT_EMOJIS = {
        "supervisor": "👔",
        "sql_agent": "🗄️",
        "analyst": "📊",
        "report_writer": "📝",
        "user": "👤"
    }
    
    # Agent names
    AGENT_NAMES = {
        "supervisor": "Supervisor",
        "sql_agent": "SQL Agent",
        "analyst": "Data Analyst",
        "report_writer": "Report Writer",
        "user": "Użytkownik"
    }
    
    # Example queries - bardziej konkretne dla logów sieciowych
    EXAMPLE_QUERIES = [
        "Stwórz raport o wykorzystaniu aplikacji - TOP 10 aplikacji",
        "Pokaż analizę aktywności użytkowników w ostatnim tygodniu",
        "Który użytkownik spędził najwięcej czasu na social media (Facebook, Instagram)?",
        "Jakie aplikacje biznesowe (Teams, Outlook) są najczęściej używane?",
        "Porównaj wykorzystanie przeglądarek (Chrome, Firefox, Edge)",
        "Które aplikacje zużywają najwięcej transferu danych (bytes_sent/received)?",
        "Analiza kategorii aplikacji - social media vs business vs inne",
        "Pokaż użytkowników z największą aktywnością sieciową",
        "Trendy czasowe - o której godzinie jest największy ruch?",
        "Które aplikacje były używane najdłużej (duration)?"
    ]