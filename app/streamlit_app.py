# app/streamlit_app.py
# Interfejs użytkownika dla systemu analizy ruchu

import streamlit as st
import pandas as pd
import plotly.express as px
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.working_system import analyze_query, check_database_stats, execute_sql_query

# Konfiguracja strony
st.set_page_config(
    page_title="Network Traffic Analyzer",
    page_icon="🌐",
    layout="wide"
)

# Tytuł
st.title("🌐 System Analizy Ruchu Sieciowego")
st.markdown("Zadaj pytanie w języku naturalnym o aktywność użytkowników")

# Sidebar z przykładami
with st.sidebar:
    st.header("📚 Przykładowe pytania")
    
    example_questions = [
        "Ile czasu spędzono na Facebooku?",
        "Kto najwięcej używał social media?",
        "Jakie są najpopularniejsze gry?",
        "Ile kosztowało nas YouTube?",
        "Pokaż produktywność zespołu",
        "Kto pracował najdłużej?",
        "Analiza użytkownika Dawid",
    ]
    
    st.markdown("Kliknij aby użyć:")
    for q in example_questions:
        if st.button(q, key=q):
            st.session_state.question = q
    
    st.markdown("---")
    
    # Statystyki
    if st.button("📊 Pokaż statystyki bazy"):
        st.session_state.show_stats = True

# Główna część
col1, col2 = st.columns([3, 1])

with col1:
    # Input pytania
    question = st.text_input(
        "Twoje pytanie:",
        value=st.session_state.get('question', ''),
        placeholder="np. Ile czasu Dawid spędził na social media?"
    )

with col2:
    analyze_button = st.button("🔍 Analizuj", type="primary", use_container_width=True)

# Analiza
if analyze_button and question:
    with st.spinner("Analizuję dane..."):
        result = analyze_query(question)
        
        if result['success']:
            # Wyświetl raport
            st.markdown("### 📊 Wyniki analizy")
            st.markdown(result['report'])
            
            # Pokaż SQL w ekspanderze
            with st.expander("🔧 Zapytanie SQL"):
                st.code(result['sql_query'], language='sql')
            
            # Wizualizacja jeśli są dane
            if result['data'] and len(result['data']) > 0:
                with st.expander("📈 Wizualizacja danych"):
                    df = pd.DataFrame(result['data'])
                    
                    # Automatyczna wizualizacja
                    if len(df) <= 20 and len(df.columns) >= 2:
                        # Wybierz typ wykresu
                        numeric_cols = df.select_dtypes(include=['float64', 'int64']).columns
                        
                        if len(numeric_cols) > 0:
                            # Wykres słupkowy
                            fig = px.bar(
                                df.head(10), 
                                x=df.columns[0], 
                                y=numeric_cols[0],
                                title=f"{numeric_cols[0]} by {df.columns[0]}"
                            )
                            st.plotly_chart(fig, use_container_width=True)
                    
                    # Tabela danych
                    st.dataframe(df, use_container_width=True)
        else:
            st.error(result['report'])

# Statystyki bazy (jeśli wybrano)
if st.session_state.get('show_stats', False):
    st.markdown("---")
    st.header("📊 Statystyki bazy danych")
    
    col1, col2, col3 = st.columns(3)
    
    # Podstawowe metryki
    with col1:
        total_records = execute_sql_query("SELECT COUNT(*) as count FROM logs")
        if not total_records.empty:
            st.metric("Liczba rekordów", f"{total_records['count'][0]:,}")
    
    with col2:
        total_users = execute_sql_query("SELECT COUNT(DISTINCT srcname) as count FROM logs")
        if not total_users.empty:
            st.metric("Liczba użytkowników", total_users['count'][0])
    
    with col3:
        date_range = execute_sql_query("SELECT MIN(date) as min_date, MAX(date) as max_date FROM logs")
        if not date_range.empty:
            st.metric("Zakres dat", f"{date_range['min_date'][0]} - {date_range['max_date'][0]}")
    
    # Kategorie aplikacji
    st.subheader("Kategorie aplikacji")
    categories = execute_sql_query("""
        SELECT appcat, COUNT(*) as sessions, SUM(duration)/3600.0 as hours 
        FROM logs 
        WHERE appcat IS NOT NULL 
        GROUP BY appcat 
        ORDER BY hours DESC
    """)
    
    if not categories.empty:
        fig = px.pie(categories, values='hours', names='appcat', title="Czas spędzony wg kategorii (godziny)")
        st.plotly_chart(fig, use_container_width=True)
    
    # Top aplikacje
    st.subheader("Top 10 aplikacji")
    top_apps = execute_sql_query("""
        SELECT app, COUNT(*) as sessions, SUM(duration)/3600.0 as hours 
        FROM logs 
        GROUP BY app 
        ORDER BY hours DESC 
        LIMIT 10
    """)
    
    if not top_apps.empty:
        fig = px.bar(top_apps, x='app', y='hours', title="Czas spędzony w aplikacjach (godziny)")
        st.plotly_chart(fig, use_container_width=True)
    
    # Resetuj flagę
    st.session_state.show_stats = False

# Stopka
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center'>
        <p>🚀 System wieloagentowy analizy ruchu sieciowego | Projekt TEG 2025</p>
    </div>
    """,
    unsafe_allow_html=True
)
