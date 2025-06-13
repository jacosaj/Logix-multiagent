"""
Multi-Agent System UI - Interfejs Streamlit z wizualizacją grafu
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


def render_graph_visualization(system):
    """Renderuj statyczną wizualizację grafu z fallbackiem"""
    from utils.visualization import GraphVisualizer
    
    st.markdown("### 🔄 Architektura systemu multi-agentowego")
    
    # Opcje renderowania
    render_option = st.radio(
        "Wybierz sposób wyświetlania:",
        ["🎨 Mermaid Diagram", "📊 HTML Fallback", "🔧 Debug"],
        horizontal=True
    )
    
    if render_option == "🎨 Mermaid Diagram":
        # Próba renderowania Mermaid
        try:
            GraphVisualizer.show_static_graph()
        except Exception as e:
            st.error(f"Błąd Mermaid: {e}")
            st.info("Przełączam na HTML Fallback...")
            render_html_fallback()
    
    elif render_option == "📊 HTML Fallback":
        render_html_fallback()
    
    elif render_option == "🔧 Debug":
        render_debug_info()
    
    # Statystyki architektury
    stats = GraphVisualizer.get_architecture_stats()
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Węzły", stats['total_nodes'])
    with col2:
        st.metric("Krawędzie", stats['total_edges'])
    with col3:
        st.metric("Agenty", stats['agent_count'])
    
    # Reszta opisu architektury...
    render_architecture_description()


def render_html_fallback():
    """Fallback HTML diagram"""
    st.markdown("#### 📊 Diagram HTML (Fallback)")
    
    html_diagram = """
    <div style="
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 30px;
        border-radius: 15px;
        color: white;
        margin: 20px 0;
    ">
        <div style="text-align: center; font-size: 24px; margin-bottom: 30px;">
            🤖 Multi-Agent System Architecture
        </div>
        
        <div style="display: flex; justify-content: center; align-items: center; flex-wrap: wrap; gap: 20px;">
            
            <!-- START -->
            <div style="
                background: #ffa07a;
                padding: 15px 25px;
                border-radius: 50px;
                font-weight: bold;
                box-shadow: 0 4px 8px rgba(0,0,0,0.2);
            ">
                🚀 START
            </div>
            
            <!-- Arrow -->
            <div style="font-size: 30px;">→</div>
            
            <!-- SUPERVISOR -->
            <div style="
                background: #ff6b6b;
                padding: 15px 25px;
                border-radius: 10px;
                font-weight: bold;
                box-shadow: 0 4px 8px rgba(0,0,0,0.2);
                text-align: center;
            ">
                👔<br>Supervisor
            </div>
            
        </div>
        
        <!-- Second row -->
        <div style="display: flex; justify-content: center; align-items: center; flex-wrap: wrap; gap: 20px; margin-top: 20px;">
            
            <div style="font-size: 30px;">↙</div>
            <div style="font-size: 30px;">↓</div>
            <div style="font-size: 30px;">↘</div>
            
        </div>
        
        <!-- Third row -->
        <div style="display: flex; justify-content: center; align-items: center; flex-wrap: wrap; gap: 30px; margin-top: 20px;">
            
            <!-- SQL AGENT -->
            <div style="
                background: #4ecdc4;
                padding: 15px 25px;
                border-radius: 10px;
                font-weight: bold;
                box-shadow: 0 4px 8px rgba(0,0,0,0.2);
                text-align: center;
            ">
                🗄️<br>SQL Agent
            </div>
            
            <!-- ANALYST -->
            <div style="
                background: #45b7d1;
                padding: 15px 25px;
                border-radius: 10px;
                font-weight: bold;
                box-shadow: 0 4px 8px rgba(0,0,0,0.2);
                text-align: center;
            ">
                📊<br>Data Analyst
            </div>
            
            <!-- REPORT WRITER -->
            <div style="
                background: #96ceb4;
                padding: 15px 25px;
                border-radius: 10px;
                font-weight: bold;
                box-shadow: 0 4px 8px rgba(0,0,0,0.2);
                text-align: center;
            ">
                📝<br>Report Writer
            </div>
            
        </div>
        
        <!-- Arrows to END -->
        <div style="display: flex; justify-content: center; align-items: center; margin-top: 20px;">
            <div style="font-size: 30px;">↘ ↓ ↙</div>
        </div>
        
        <!-- END -->
        <div style="display: flex; justify-content: center; margin-top: 20px;">
            <div style="
                background: #dda0dd;
                padding: 15px 25px;
                border-radius: 50px;
                font-weight: bold;
                box-shadow: 0 4px 8px rgba(0,0,0,0.2);
            ">
                🏁 END
            </div>
        </div>
        
        <!-- Note -->
        <div style="text-align: center; margin-top: 30px; font-size: 14px; opacity: 0.8;">
            ⚡ Wszystkie agenty mogą komunikować się między sobą<br>
            🔄 Inteligentny routing na podstawie kontekstu zadania
        </div>
        
    </div>
    """
    
    st.markdown(html_diagram, unsafe_allow_html=True)


def render_debug_info():
    """Debug info dla problemu z Mermaid"""
    st.markdown("#### 🔧 Informacje diagnostyczne")
    
    # Test podstawowego HTML
    st.markdown("**Test 1: Podstawowy HTML**")
    st.markdown('<div style="background: red; color: white; padding: 10px;">Test HTML działa</div>', unsafe_allow_html=True)
    
    # Test JavaScript
    st.markdown("**Test 2: Test JavaScript**")
    js_test = """
    <div id="js-test">JavaScript nie działa</div>
    <script>
        document.getElementById('js-test').innerHTML = 'JavaScript działa!';
        document.getElementById('js-test').style.background = 'green';
        document.getElementById('js-test').style.color = 'white';
        document.getElementById('js-test').style.padding = '10px';
    </script>
    """
    st.components.v1.html(js_test, height=100)
    
    # Test zewnętrznego CDN
    st.markdown("**Test 3: Zewnętrzny CDN**")
    cdn_test = """
    <div id="cdn-test">Ładowanie CDN...</div>
    <script src="https://cdn.jsdelivr.net/npm/mermaid@10.6.1/dist/mermaid.min.js"></script>
    <script>
        if (typeof mermaid !== 'undefined') {
            document.getElementById('cdn-test').innerHTML = 'Mermaid CDN załadowany ✅';
            document.getElementById('cdn-test').style.background = 'green';
        } else {
            document.getElementById('cdn-test').innerHTML = 'Mermaid CDN NIE załadowany ❌';
            document.getElementById('cdn-test').style.background = 'red';
        }
        document.getElementById('cdn-test').style.color = 'white';
        document.getElementById('cdn-test').style.padding = '10px';
    </script>
    """
    st.components.v1.html(cdn_test, height=100)
    
    # Minimal Mermaid test
    st.markdown("**Test 4: Minimalny Mermaid**")
    minimal_mermaid = """
    <div class="mermaid">
        graph TD
            A[Hello] --> B[World]
    </div>
    <script src="https://cdn.jsdelivr.net/npm/mermaid@10.6.1/dist/mermaid.min.js"></script>
    <script>
        mermaid.initialize({startOnLoad:true});
    </script>
    """
    st.components.v1.html(minimal_mermaid, height=200)
    
    # Kod Mermaid do skopiowania
    st.markdown("**Test 5: Kod do skopiowania**")
    from utils.visualization import GraphVisualizer
    mermaid_code = GraphVisualizer.get_static_mermaid_code()
    st.code(mermaid_code, language="text")
    
    st.info("💡 Możesz skopiować kod i wkleić na https://mermaid.live/ aby sprawdzić czy działa")


def render_architecture_description():
    """Reszta opisu architektury"""
    st.markdown("---")
    st.markdown("### 📋 Opis architektury")
    
    st.markdown("""
    **🔄 Inteligentny routing:**
    - System używa **conditional edges** - każdy agent może przekierować do różnych agentów
    - Decyzje podejmowane na podstawie stanu zadania i wyników poprzedniego agenta
    - Możliwość powrotu do Supervisor przy błędach lub potrzebie zmiany strategii
    
    **👔 Supervisor** - Punkt centralny:
    - Analizuje zapytanie użytkownika
    - Decyduje o kolejności agentów
    - Zarządza przepływem i obsługą błędów
    
    **🗄️ SQL Agent** - Dostęp do danych:
    - Wykonuje zapytania do bazy logów sieciowych
    - Może wrócić do Supervisor jeśli brak danych
    - Przekazuje wyniki do Analyst lub bezpośrednio do Report Writer
    
    **📊 Data Analyst** - Analiza danych:
    - Przetwarza dane z SQL Agent
    - Tworzy statystyki, trendy i wnioski
    - Może zażądać dodatkowych danych od SQL Agent
    
    **📝 Report Writer** - Raportowanie:
    - Tworzy końcowy raport na podstawie analizy
    - Formatuje wyniki w czytelny sposób
    - Może wrócić do Supervisor w przypadku problemów
    """)
    
    # Przykładowe ścieżki
    st.markdown("### 🛣️ Typowe ścieżki przepływu")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        **📊 Standardowy raport:**
        ```
        START → Supervisor → SQL Agent 
              → Analyst → Report Writer → END
        ```
        
        **🔍 Zapytanie o dane:**
        ```
        START → Supervisor → SQL Agent → END
        ```
        """)
    
    with col2:
        st.markdown("""
        **⚠️ Obsługa błędów:**
        ```
        START → Supervisor → SQL Agent 
              → Supervisor → Report Writer → END
        ```
        
        **🔄 Iteracyjna analiza:**
        ```
        START → Supervisor → SQL Agent → Analyst 
              → SQL Agent → Analyst → Report Writer → END
        ```
        """)
    
    # Opcja eksportu
    st.markdown("---")
    if st.button("💾 Eksportuj architekturę do HTML"):
        from utils.visualization import GraphVisualizer
        filename = GraphVisualizer.export_to_html()
        st.success(f"✅ Wyeksportowano do: {filename}")
        
        with open(filename, 'r', encoding='utf-8') as f:
            st.download_button(
                label="📥 Pobierz HTML",
                data=f.read(),
                file_name=filename,
                mime="text/html"
            )


def main():
    # Nagłówek
    st.markdown('<h1 class="main-header">🤖 Multi-Agent System</h1>', unsafe_allow_html=True)
    st.markdown("### Wieloagentowy analizator logów sieciowych")
    
    # Inicjalizuj system
    with st.spinner("🔄 Inicjalizuję system multi-agentowy..."):
        system, error = initialize_multi_agent_system()
    
    if error:
        st.error(f"❌ Błąd inicjalizacji: {error}")
        st.info("💡 Sprawdź konfigurację i klucz API")
        return
    
    # Tabs dla różnych sekcji
    tab1, tab2 = st.tabs(["💬 Chat", "🔄 Graf"])
    
    with tab1:
        render_chat_interface(system)
    
    with tab2:
        render_graph_visualization(system)


def render_chat_interface(system):
    """Renderuj interfejs chatu"""
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
    user_input = st.chat_input("Zadaj pytanie...")
    
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