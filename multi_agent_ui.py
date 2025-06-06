"""
Multi-Agent System UI - Interfejs Streamlit
"""
import streamlit as st
from datetime import datetime

from langgraph_multi_agent import MultiAgentSystem
from config.settings import Config

# Konfiguracja strony
st.set_page_config(
    page_title=Config.PAGE_TITLE,
    page_icon=Config.PAGE_ICON,
    layout=Config.LAYOUT,
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

.agent-message {
    padding: 1rem;
    border-radius: 10px;
    margin: 1rem 0;
    border-left: 4px solid;
}

.supervisor-msg {
    background-color: #e3f2fd;
    border-left-color: #1976d2;
}

.sql-agent-msg {
    background-color: #f3e5f5;
    border-left-color: #7b1fa2;
}

.analyst-msg {
    background-color: #e8f5e9;
    border-left-color: #388e3c;
}

.report-writer-msg {
    background-color: #fff3e0;
    border-left-color: #f57c00;
}

.user-msg {
    background-color: #f0f8ff;
    border-left-color: #4caf50;
}

.agent-badge {
    display: inline-block;
    padding: 0.25rem 0.75rem;
    border-radius: 15px;
    font-size: 0.875rem;
    font-weight: bold;
    margin-bottom: 0.5rem;
}

.supervisor-badge { background-color: #1976d2; color: white; }
.sql-badge { background-color: #7b1fa2; color: white; }
.analyst-badge { background-color: #388e3c; color: white; }
.report-badge { background-color: #f57c00; color: white; }

.sidebar-info {
    background-color: #f0f8ff;
    padding: 1rem;
    border-radius: 8px;
    margin: 1rem 0;
}

.flow-diagram {
    background-color: #fafafa;
    border: 2px solid #e0e0e0;
    border-radius: 10px;
    padding: 1.5rem;
    margin: 1rem 0;
    text-align: center;
}

.metrics-card {
    background-color: #f5f5f5;
    border-radius: 8px;
    padding: 1rem;
    margin: 0.5rem 0;
    border-left: 3px solid #1e88e5;
}
</style>
""", unsafe_allow_html=True)

# Załaduj zmienne środowiskowe


def get_agent_emoji(agent_type: str) -> str:
    """Zwróć emoji dla danego typu agenta"""
    return Config.AGENT_EMOJIS.get(agent_type, "🤖")


def get_agent_name(agent_type: str) -> str:
    """Zwróć nazwę agenta"""
    return Config.AGENT_NAMES.get(agent_type, "Agent")


def get_message_class(agent_type: str) -> str:
    """Zwróć klasę CSS dla wiadomości"""
    classes = {
        "supervisor": "supervisor-msg",
        "sql_agent": "sql-agent-msg",
        "analyst": "analyst-msg",
        "report_writer": "report-writer-msg",
        "user": "user-msg"
    }
    return classes.get(agent_type, "agent-message")


def get_badge_class(agent_type: str) -> str:
    """Zwróć klasę CSS dla badge"""
    classes = {
        "supervisor": "supervisor-badge",
        "sql_agent": "sql-badge",
        "analyst": "analyst-badge",
        "report_writer": "report-badge"
    }
    return classes.get(agent_type, "agent-badge")


@st.cache_resource
def initialize_multi_agent_system():
    """Inicjalizuj system multi-agentowy"""
    try:
        system = MultiAgentSystem()
        return system, None
    except Exception as e:
        return None, str(e)


def display_agent_flow():
    """Wyświetl diagram przepływu agentów"""
    st.markdown("""
    <div class="flow-diagram">
    <h4>🔄 Przepływ między agentami</h4>
    <p style="font-family: monospace; font-size: 14px;">
    👤 User → 👔 Supervisor → 🗄️ SQL Agent ↔ 📊 Data Analyst → 📝 Report Writer
    </p>
    </div>
    """, unsafe_allow_html=True)


def main():
    # Nagłówek
    st.markdown('<h1 class="main-header">🤖 Multi-Agent System</h1>', unsafe_allow_html=True)
    st.markdown("### System wielu agentów współpracujących ze sobą")
    
    # Wyświetl diagram przepływu
    display_agent_flow()
    
    # Inicjalizuj system
    with st.spinner("🔄 Inicjalizuję system multi-agentowy..."):
        system, error = initialize_multi_agent_system()
    
    if error:
        st.error(f"❌ Błąd inicjalizacji: {error}")
        st.info("💡 Sprawdź konfigurację i klucz API")
        return
    
    # Sidebar z informacjami
    with st.sidebar:
        st.header("🤖 O systemie")
        
        st.markdown("""
        <div class="sidebar-info">
        <h4>Agenci w systemie:</h4>
        
        **👔 Supervisor**
        - Zarządza przepływem zadań
        - Decyduje który agent powinien wykonać zadanie
        
        **🗄️ SQL Agent**
        - Wykonuje zapytania do bazy danych
        - Pobiera dane z logów sieciowych
        
        **📊 Data Analyst**
        - Analizuje dane z SQL
        - Tworzy statystyki i wnioski
        
        **📝 Report Writer**
        - Tworzy profesjonalne raporty
        - Formatuje wyniki w czytelny sposób
        </div>
        """, unsafe_allow_html=True)
        
        st.header("💡 Przykładowe zapytania")
        
        for i, query in enumerate(Config.EXAMPLE_QUERIES):
            if st.button(f"🔍 {query}", key=f"example_{i}"):
                st.session_state.current_query = query
        
        # Statystyki sesji
        if "process_count" in st.session_state:
            st.header("📈 Statystyki sesji")
            st.markdown(f"""
            <div class="metrics-card">
            • Zapytań: {st.session_state.process_count}<br>
            • Agentów użytych: {len(st.session_state.get('agents_used', set()))}<br>
            • Czas sesji: {datetime.now().strftime('%H:%M')}
            </div>
            """, unsafe_allow_html=True)
    
    # Inicjalizuj session state
    if "messages" not in st.session_state:
        st.session_state.messages = []
        st.session_state.process_count = 0
        st.session_state.agents_used = set()
    
    # Wyświetl historię
    for message in st.session_state.messages:
        agent_type = message.get("agent", "assistant")
        msg_class = get_message_class(agent_type)
        emoji = get_agent_emoji(agent_type)
        name = get_agent_name(agent_type)
        
        if agent_type != "user":
            badge_class = get_badge_class(agent_type)
            st.markdown(f"""
            <div class="agent-message {msg_class}">
                <span class="agent-badge {badge_class}">{emoji} {name}</span>
                <div>{message['content']}</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            with st.chat_message("user"):
                st.write(message['content'])
    
    # Input użytkownika
    user_input = st.chat_input("Zadaj pytanie systemowi agentów...")
    
    # Obsługa przykładowych zapytań
    if "current_query" in st.session_state:
        user_input = st.session_state.current_query
        del st.session_state.current_query
    
    if user_input:
        # Dodaj pytanie użytkownika
        st.session_state.messages.append({
            "agent": "user",
            "content": user_input
        })
        
        # Wyświetl pytanie
        with st.chat_message("user"):
            st.write(user_input)
        
        # Przetwórz przez system
        with st.spinner("🤔 Agenci pracują nad odpowiedzią..."):
            col1, col2 = st.columns([3, 1])
            
            with col1:
                # Placeholder dla statusu
                status_placeholder = st.empty()
            
            try:
                # Uruchom system
                result = system.process(user_input)
                
                # Pobierz historię konwersacji
                history = system.get_conversation_history(result)
                
                # Dodaj wiadomości agentów do historii (pomijając pierwszą - pytanie użytkownika)
                for entry in history[1:]:
                    if entry['role'] != 'user':
                        st.session_state.messages.append({
                            "agent": entry['role'],
                            "content": entry['content']
                        })
                        
                        # Aktualizuj zestaw użytych agentów
                        st.session_state.agents_used.add(entry['role'])
                
                # Zwiększ licznik
                st.session_state.process_count += 1
                
                # Odśwież stronę aby pokazać nowe wiadomości
                st.rerun()
                
            except Exception as e:
                st.error(f"❌ Błąd podczas przetwarzania: {str(e)}")
    
    # Przyciski akcji
    col1, col2, col3 = st.columns([1, 1, 3])
    
    with col1:
        if st.button("🗑️ Wyczyść historię"):
            st.session_state.messages = []
            st.session_state.process_count = 0
            st.session_state.agents_used = set()
            st.rerun()
    
    with col2:
        if st.button("📊 Pokaż stan systemu"):
            if system and hasattr(system, 'sql_agent'):
                stats = system.sql_agent.get_database_stats()
                st.json(stats)
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: #666;'>
    🤖 Multi-Agent System | Powered by LangGraph & LangChain | 
    <a href='https://langchain-ai.github.io/langgraph/' target='_blank'>LangGraph Docs</a>
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()