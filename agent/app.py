import streamlit as st
import os
from datetime import datetime
from dotenv import load_dotenv

# Import modułu SQL agenta
from sql_agent import SQLAgent

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
def initialize_sql_agent():
    """Inicjalizuj SQL agenta - cache dla wydajności"""
    try:
        agent = SQLAgent()
        success, error = agent.initialize()
        
        if success:
            return agent, None
        else:
            return None, error
    except Exception as e:
        return None, str(e)


def main():
    # Nagłówek
    st.markdown('<h1 class="main-header">🤖 SQL Chat Agent</h1>', unsafe_allow_html=True)
    st.markdown("### Zadawaj pytania o dane sieciowe w naturalnym języku!")
    
    # Inicjalizuj agenta
    with st.spinner("🔄 Inicjalizuję SQL agenta..."):
        agent, error = initialize_sql_agent()
    
    if error:
        st.error(f"❌ Błąd inicjalizacji: {error}")
        st.info("💡 Sprawdź czy masz plik logs.db lub CSV z danymi")
        st.info("💡 Upewnij się, że zmienna OPENAI_API_KEY_TEG jest ustawiona")
        return
    
    # Sidebar z informacjami
    with st.sidebar:
        st.header("📊 Informacje o bazie")
        
        if agent:
            # Pobierz statystyki
            stats = agent.get_database_stats()
            
            if 'error' not in stats:
                st.success(f"✅ Baza: {os.path.basename(stats['db_path'])}")
                
                st.markdown(f"""
                <div class="sidebar-info">
                <strong>📈 Statystyki:</strong><br>
                • Rekordów: {stats['total_rows']:,}<br>
                • Użytkowników: {stats['unique_users']}<br>
                • Aplikacji: {stats['unique_apps']}<br>
                • Okres: {stats['date_range'][0]} - {stats['date_range'][1]}
                </div>
                """, unsafe_allow_html=True)
            else:
                st.error(f"Błąd pobierania statystyk: {stats['error']}")
        
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
                # Zapytaj agenta
                result = agent.query(user_input)
                
                if result["success"]:
                    # Wyświetl odpowiedź
                    st.write(result["output"])
                    
                    # Dodaj odpowiedź do historii
                    st.session_state.messages.append({
                        "role": "assistant", 
                        "content": result["output"]
                    })
                else:
                    error_msg = f"❌ Przepraszam, wystąpił błąd: {result['error']}"
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