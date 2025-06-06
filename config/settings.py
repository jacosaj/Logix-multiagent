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
    MAX_ITERATIONS = 10
    VERBOSE = False
    
    # Database paths
    DB_SEARCH_PATHS = [
        "./logs.db",
        "./parser/logs.db", 
        "../parser/logs.db",
        "logs.db",
        "./data/logs.db"
    ]
    
    # UI settings
    PAGE_TITLE = "�� Multi-Agent System"
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
    
    # Example queries
    EXAMPLE_QUERIES = [
        "Pokaż analizę aktywności użytkowników",
        "Kto najdłużej korzystał z social media?",
        "Stwórz raport o wykorzystaniu aplikacji",
        "Analizuj trendy w wykorzystaniu sieci",
        "Które aplikacje zużywają najwięcej danych?",
        "Porównaj aktywność użytkowników w tym tygodniu"
    ]
