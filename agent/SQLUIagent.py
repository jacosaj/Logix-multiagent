import streamlit as st
import os
import sqlite3
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv

from langchain_openai import ChatOpenAI
from langchain_community.utilities.sql_database import SQLDatabase
from langchain_community.agent_toolkits.sql.toolkit import SQLDatabaseToolkit
from langchain_community.agent_toolkits.sql.base import create_sql_agent
from langchain.agents.agent_types import AgentType

# Konfiguracja strony
st.set_page_config(
    page_title="🤖 SQL Chat Agent",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS dla lepszego wyglądu
st.markdown("""
<style>
.main-header {
    font-size: 2.5rem;
    font-weight: bold;
    text-align: center;
    color: #1e88e5;
    margin-bottom: 2rem;
}

.chat-message {
    padding: 1rem;
    border-radius: 10px;
    margin: 1rem 0;
    border-left: 4px solid #1e88e5;
}

.user-message {
    background-color: #f0f8ff;
    border-left-color: #4caf50;
}

.bot-message {
    background-color: #f5f5f5;
    border-left-color: #1e88e5;
}

.error-message {
    background-color: #ffebee;
    border-left-color: #f44336;
    color: #d32f2f;
}

.success-message {
    background-color: #e8f5e8;
    border-left-color: #4caf50;
    color: #2e7d32;
}

.sidebar-info {
    background-color: #f0f8ff;
    padding: 1rem;
    border-radius: 8px;
    margin: 1rem 0;
}
</style>
""", unsafe_allow_html=True)

# Załaduj zmienne środowiskowe
load_dotenv()

@st.cache_resource
def initialize_agent():
    """Inicjalizuj SQL agenta - cache dla wydajności"""
    
    # Możliwe lokalizacje bazy danych
    possible_db_paths = [
        "./logs.db",
        "./parser/logs.db", 
        "../parser/logs.db",
        "logs.db",
        "./data/logs.db"
    ]
    
    # Znajdź bazę danych
    db_path = None
    for path in possible_db_paths:
        if os.path.exists(path):
            db_path = path
            break
    
    # Jeśli nie ma bazy, spróbuj utworzyć z CSV
    if not db_path:
        csv_files = [f for f in os.listdir('.') if 'logi' in f.lower() and f.endswith('.csv')]
        if csv_files:
            try:
                csv_file = csv_files[0]
                db_path = "logs.db"
                
                df = pd.read_csv(csv_file)
                conn = sqlite3.connect(db_path)
                df.to_sql('logs', conn, if_exists='replace', index=False)
                conn.close()
                
                st.success(f"✅ Utworzono bazę z pliku CSV: {csv_file}")
            except Exception as e:
                st.error(f"❌ Błąd tworzenia bazy: {e}")
                return None, None, str(e)
    
    if not db_path:
        return None, None, "Brak bazy danych"
    
    try:
        # Inicjalizuj LLM
        llm = ChatOpenAI(
            model_name="gpt-4o-mini",
            openai_api_key=os.environ.get('OPENAI_API_KEY_TEG'),
            temperature=0,
        )
        
        # Połącz z bazą
        db = SQLDatabase.from_uri(f"sqlite:///{db_path}")
        
        # Utwórz agenta
        toolkit = SQLDatabaseToolkit(db=db, llm=llm)
        
        agent = create_sql_agent(
            llm=llm,
            toolkit=toolkit,
            agent_type=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
            verbose=False,  # Wyłącz verbose dla Streamlit
            max_iterations=10,
            early_stopping_method="generate"
        )
        
        return agent, db_path, None
        
    except Exception as e:
        return None, None, str(e)

def get_database_stats(db_path):
    """Pobierz statystyki bazy danych"""
    try:
        conn = sqlite3.connect(db_path)
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
            'unique_apps': unique_apps
        }
    except Exception as e:
        return {'error': str(e)}

def format_response(response):
    """Formatuj odpowiedź agenta"""
    if isinstance(response, dict) and 'output' in response:
        return response['output']
    return str(response)

def main():
    # Nagłówek
    st.markdown('<h1 class="main-header">🤖 SQL Chat Agent</h1>', unsafe_allow_html=True)
    st.markdown("### Zadawaj pytania o dane sieciowe w naturalnym języku!")
    
    # Inicjalizuj agenta
    with st.spinner("🔄 Inicjalizuję SQL agenta..."):
        agent, db_path, error = initialize_agent()
    
    if error:
        st.error(f"❌ Błąd inicjalizacji: {error}")
        st.info("💡 Sprawdź czy masz plik logs.db lub CSV z danymi")
        return
    
    # Sidebar z informacjami
    with st.sidebar:
        st.header("📊 Informacje o bazie")
        
        if db_path:
            st.success(f"✅ Baza: {os.path.basename(db_path)}")
            
            # Statystyki bazy
            stats = get_database_stats(db_path)
            if 'error' not in stats:
                st.markdown(f"""
                <div class="sidebar-info">
                <strong>📈 Statystyki:</strong><br>
                • Rekordów: {stats['total_rows']:,}<br>
                • Użytkowników: {stats['unique_users']}<br>
                • Aplikacji: {stats['unique_apps']}<br>
                • Okres: {stats['date_range'][0]} - {stats['date_range'][1]}
                </div>
                """, unsafe_allow_html=True)
        
        st.header("💡 Przykładowe pytania")
        example_questions = [
            "Ile mamy użytkowników?",
            "Kto najdłużej korzystał z Facebooka?",
            "Pokaż top 5 aplikacji",
            "Ile czasu spędził Dawid na grach?",
            "Które aplikacje są z kategorii Social.Media?",
            "Kto przesłał najwięcej danych?",
            "Pokaż aktywność w godzinach 9-17",
            "Jakie są kategorie aplikacji?"
        ]
        
        for i, question in enumerate(example_questions):
            if st.button(f"📝 {question}", key=f"example_{i}"):
                st.session_state.current_question = question
    
    # Inicjalizuj session state
    if "messages" not in st.session_state:
        st.session_state.messages = []
        st.session_state.messages.append({
            "role": "assistant", 
            "content": "👋 Cześć! Jestem SQL agentem. Mogę odpowiadać na pytania o Twoje dane sieciowe. Zadaj mi pytanie!"
        })
    
    # Wyświetl historię czatu
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])
    
    # Input użytkownika
    user_input = st.chat_input("Zadaj pytanie o dane...")
    
    # Obsługa przykładowych pytań z sidebara
    if "current_question" in st.session_state:
        user_input = st.session_state.current_question
        del st.session_state.current_question
    
    if user_input:
        # Dodaj pytanie użytkownika do historii
        st.session_state.messages.append({"role": "user", "content": user_input})
        
        # Wyświetl pytanie użytkownika
        with st.chat_message("user"):
            st.write(user_input)
        
        # Generuj odpowiedź
        with st.chat_message("assistant"):
            with st.spinner("🤔 Myślę..."):
                try:
                    # Zapytaj agenta
                    response = agent.invoke({"input": user_input})
                    answer = format_response(response)
                    
                    # Wyświetl odpowiedź
                    st.write(answer)
                    
                    # Dodaj odpowiedź do historii
                    st.session_state.messages.append({
                        "role": "assistant", 
                        "content": answer
                    })
                    
                except Exception as e:
                    error_msg = f"❌ Przepraszam, wystąpił błąd: {str(e)}"
                    st.error(error_msg)
                    st.session_state.messages.append({
                        "role": "assistant", 
                        "content": error_msg
                    })
    
    # Przycisk czyszczenia historii
    if st.button("🗑️ Wyczyść historię czatu"):
        st.session_state.messages = []
        st.session_state.messages.append({
            "role": "assistant", 
            "content": "👋 Historia została wyczyszczona. Zadaj mi nowe pytanie!"
        })
        st.rerun()
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: #666;'>
    🤖 SQL Chat Agent | Powered by LangChain & OpenAI | 
    <a href='https://streamlit.io' target='_blank'>Streamlit</a>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()