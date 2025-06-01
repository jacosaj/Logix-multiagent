# Ulepszona implementacja systemu wieloagentowego
# Plik: agents/improved_system.py

import os
import re
from typing import Annotated, Literal, TypedDict, Dict, List
from datetime import datetime
import sqlite3
import pandas as pd

from langchain_openai import ChatOpenAI
from langchain_community.utilities.sql_database import SQLDatabase
from langchain.agents.agent_toolkits import SQLDatabaseToolkit
from langchain.tools import Tool
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage
from langgraph.graph import END, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from dotenv import load_dotenv

load_dotenv()

# ===== KONFIGURACJA =====
class Config:
    DB_PATH = r"/Users/fmpl5278/Desktop/Logi-projektTEG/parser/logs.db"
    DEFAULT_HOURLY_RATE = 150  # PLN/h - realistyczna stawka dla IT
    GOLD_PRICE_PLN = 280  # cena za gram
    BTC_PRICE_PLN = 180000
    USD_RATE = 4.05
    EUR_RATE = 4.30
    GBP_RATE = 5.10

# ===== INICJALIZACJA =====
llm = ChatOpenAI(
    model_name="gpt-4o-mini",
    openai_api_key=os.environ['OPENAI_API_KEY_TEG'],
    temperature=0,
)

sql_db = SQLDatabase.from_uri(f"sqlite:///{Config.DB_PATH}")
sql_toolkit = SQLDatabaseToolkit(db=sql_db, llm=llm)

# ===== ULEPSZONE NARZĘDZIA =====

def calculate_comprehensive_loss(time_lost_seconds: int, hourly_rate: float = Config.DEFAULT_HOURLY_RATE) -> Dict:
    """
    Oblicza stratę w różnych walutach i aktywach
    """
    hours = time_lost_seconds / 3600
    pln_loss = hours * hourly_rate
    
    return {
        "hours": round(hours, 2),
        "minutes": round((time_lost_seconds % 3600) / 60, 0),
        "pln": round(pln_loss, 2),
        "usd": round(pln_loss / Config.USD_RATE, 2),
        "eur": round(pln_loss / Config.EUR_RATE, 2),
        "gbp": round(pln_loss / Config.GBP_RATE, 2),
        "gold_grams": round(pln_loss / Config.GOLD_PRICE_PLN, 3),
        "btc": round(pln_loss / Config.BTC_PRICE_PLN, 6),
        "coffee_cups": round(pln_loss / 15, 0),  # Średnia cena kawy
        "netflix_months": round(pln_loss / 60, 1),  # Abonament Netflix
    }

def analyze_productivity_patterns(user: str = None, date_from: str = None, date_to: str = None) -> Dict:
    """
    Analizuje wzorce produktywności użytkownika lub zespołu
    """
    conn = sqlite3.connect(Config.DB_PATH)
    
    # Podstawowe zapytanie
    base_query = """
    SELECT 
        srcname,
        appcat,
        DATE(date) as day,
        strftime('%H', time) as hour,
        SUM(duration) as total_seconds,
        COUNT(*) as sessions
    FROM network_logs
    WHERE 1=1
    """
    
    # Dodaj filtry
    params = []
    if user:
        base_query += " AND srcname LIKE ?"
        params.append(f"%{user}%")
    
    if date_from:
        base_query += " AND date >= ?"
        params.append(date_from)
        
    if date_to:
        base_query += " AND date <= ?"
        params.append(date_to)
    
    base_query += " GROUP BY srcname, appcat, day, hour"
    
    df = pd.read_sql_query(base_query, conn, params=params)
    conn.close()
    
    # Analiza wzorców
    productivity_categories = ['Business', 'Development']
    unproductive_categories = ['Social.Media', 'Game', 'Adult']
    
    productive_time = df[df['appcat'].isin(productivity_categories)]['total_seconds'].sum()
    unproductive_time = df[df['appcat'].isin(unproductive_categories)]['total_seconds'].sum()
    
    # Najgorsze godziny
    worst_hours = df[df['appcat'].isin(unproductive_categories)].groupby('hour')['total_seconds'].sum().nlargest(3)
    
    return {
        "productive_hours": round(productive_time / 3600, 2),
        "unproductive_hours": round(unproductive_time / 3600, 2),
        "productivity_ratio": round(productive_time / (productive_time + unproductive_time) if (productive_time + unproductive_time) > 0 else 0, 2),
        "worst_hours": worst_hours.to_dict(),
        "total_users": df['srcname'].nunique(),
        "most_used_unproductive_app": df[df['appcat'].isin(unproductive_categories)].groupby('appcat')['total_seconds'].sum().idxmax() if not df[df['appcat'].isin(unproductive_categories)].empty else None
    }

def get_user_summary(identifier: str) -> str:
    """
    Pobiera podsumowanie aktywności użytkownika na podstawie nazwy, IP lub MAC
    """
    conn = sqlite3.connect(Config.DB_PATH)
    
    # Sprawdź czy to MAC, IP czy nazwa
    if re.match(r'^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$', identifier):
        condition = "mastersrcmac = ?"
    elif re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$', identifier):
        condition = "srcip = ?"
    else:
        condition = "srcname LIKE ?"
        identifier = f"%{identifier}%"
    
    query = f"""
    SELECT 
        srcname,
        srcip,
        mastersrcmac,
        appcat,
        app,
        SUM(duration) as total_seconds,
        COUNT(*) as sessions,
        AVG(sentbyte + rcvdbyte) as avg_traffic
    FROM network_logs
    WHERE {condition}
    GROUP BY srcname, srcip, mastersrcmac, appcat, app
    ORDER BY total_seconds DESC
    """
    
    df = pd.read_sql_query(query, conn, params=[identifier])
    conn.close()
    
    if df.empty:
        return "Nie znaleziono użytkownika"
    
    # Formatuj wyniki
    user_info = df.iloc[0]
    summary = f"Użytkownik: {user_info['srcname']} (IP: {user_info['srcip']}, MAC: {user_info['mastersrcmac']})\n\n"
    summary += "Top 5 aplikacji:\n"
    
    for _, row in df.head(5).iterrows():
        hours = row['total_seconds'] / 3600
        summary += f"- {row['app']} ({row['appcat']}): {hours:.1f}h w {row['sessions']} sesjach\n"
    
    return summary

# ===== ULEPSZONE PROMPTY =====

SEARCH_PROMPT = """Jesteś ekspertem SQL analizującym logi sieciowe. Twoje zadanie to konwersja pytań użytkownika na zapytania SQL.

STRUKTURA TABELI network_logs:
- date (DATE): data zdarzenia
- time (TIME): czas zdarzenia  
- srcname (TEXT): nazwa użytkownika
- srcip (TEXT): IP źródłowe
- mastersrcmac (TEXT): adres MAC
- app (TEXT): nazwa aplikacji
- appcat (TEXT): kategoria (Social.Media, Game, Adult, Business, Development)
- duration (INTEGER): czas trwania w SEKUNDACH
- action (TEXT): typ akcji (close, open, etc.)
- sentbyte, rcvdbyte: transfer danych

WAŻNE ZASADY:
1. Duration jest w SEKUNDACH - pamiętaj o konwersji na godziny/minuty
2. Używaj LIKE dla wyszukiwania częściowego (np. srcname LIKE '%Dawid%')
3. Daty formatuj jako 'YYYY-MM-DD'
4. Zawsze używaj GROUP BY gdy używasz funkcji agregujących
5. Dla MAC adresów używaj dokładnego dopasowania

PRZYKŁADY:
- "Ile czasu Dawid spędził na FB?" → SELECT srcname, app, SUM(duration) as total_seconds FROM network_logs WHERE srcname LIKE '%Dawid%' AND app LIKE '%Facebook%' GROUP BY srcname, app
- "Kto najwięcej gra?" → SELECT srcname, SUM(duration) as total_seconds FROM network_logs WHERE appcat = 'Game' GROUP BY srcname ORDER BY total_seconds DESC LIMIT 10

Generuj TYLKO zapytanie SQL, bez dodatkowych komentarzy."""

VALUE_PROMPT = """Jesteś agentem finansowym. Otrzymujesz dane o czasie (w sekundach) i obliczasz straty finansowe.

STAWKI:
- Godzinowa: 150 PLN (średnia w IT)
- Kawa: 15 PLN
- Netflix: 60 PLN/miesiąc
- Gram złota: 280 PLN
- Bitcoin: 180,000 PLN

Przedstaw wyniki w czytelny sposób, np.:
"Stracony czas: X godzin Y minut
Koszt: Z PLN (równowartość A kaw lub B gramów złota)"

Używaj praktycznych porównań, które pomogą zrozumieć skalę straty."""

NATURAL_PROMPT = """Jesteś asystentem analizującym ruch sieciowy. Otrzymujesz wyniki zapytań SQL i przekształcasz je w przyjazne odpowiedzi.

ZASADY:
1. Używaj prostego, zrozumiałego języka
2. Konwertuj sekundy na godziny i minuty (np. 3665 sekund = 1 godzina 1 minuta)
3. Grupuj dane logicznie (np. po kategoriach aplikacji)
4. Dodawaj kontekst (np. "To stanowi 20% czasu pracy")
5. Używaj emotikonów dla lepszej czytelności 📊

PRZYKŁAD:
Zamiast: "duration: 7200"
Napisz: "Spędził 2 godziny na tej aplikacji 🕐"
"""

# ===== ULEPSZONE NARZĘDZIA =====

tools = [
    Tool.from_function(
        func=calculate_comprehensive_loss,
        name="calculate_loss",
        description="Oblicza straty w różnych walutach. Wymaga: time_lost_seconds (int), opcjonalnie hourly_rate (float)"
    ),
    Tool.from_function(
        func=analyze_productivity_patterns,
        name="analyze_productivity",
        description="Analizuje wzorce produktywności. Parametry: user (str), date_from (YYYY-MM-DD), date_to (YYYY-MM-DD)"
    ),
    Tool.from_function(
        func=get_user_summary,
        name="get_user_summary",
        description="Pobiera podsumowanie użytkownika. Parametr: identifier (nazwa/IP/MAC)"
    ),
] + sql_toolkit.get_tools()

# ===== ULEPSZONE WĘZŁY =====

class ImprovedAgentState(TypedDict):
    messages: Annotated[list, add_messages]
    no_of_iterations: int
    sql_query: str  # Przechowuj zapytanie SQL
    raw_data: str   # Przechowuj surowe dane
    context: Dict   # Kontekst dla lepszego zrozumienia

def improved_search_node(state):
    """Ulepszona wersja search node z lepszym debugowaniem"""
    print(f"\n[SEARCH] Otrzymane pytanie: {state['messages'][-1].content}")
    
    # Wyciągnij kontekst z pytania
    question = state['messages'][-1].content.lower()
    context = {
        "has_time_query": any(word in question for word in ['czas', 'godzin', 'minut', 'spędził', 'stracił']),
        "has_user_query": any(word in question for word in ['użytkownik', 'kto', 'osoba']),
        "has_cost_query": any(word in question for word in ['koszt', 'stracił', 'pieniądze', 'złoto', 'btc']),
        "time_period": extract_time_period(question)
    }
    
    result = search_agent.invoke(state)
    
    # Zapisz zapytanie SQL
    sql_query = extract_sql_from_response(result.content)
    
    return {
        "messages": state["messages"] + [result],
        "no_of_iterations": state["no_of_iterations"] + 1,
        "sql_query": sql_query,
        "context": context
    }

def extract_time_period(question: str) -> str:
    """Wyciąga okres czasu z pytania"""
    if "dzisiaj" in question:
        return datetime.now().strftime("%Y-%m-%d")
    elif "wczoraj" in question:
        return (datetime.now() - pd.Timedelta(days=1)).strftime("%Y-%m-%d")
    elif "tydzień" in question or "tygodniu" in question:
        return "last_week"
    elif "miesiąc" in question or "miesiącu" in question:
        return "last_month"
    return "all_time"

def extract_sql_from_response(response: str) -> str:
    """Wyciąga czyste SQL z odpowiedzi"""
    # Usuń markdown i inne śmieci
    sql = response.strip()
    sql = re.sub(r'```sql\s*', '', sql)
    sql = re.sub(r'```\s*', '', sql)
    sql = re.sub(r'SQLQuery:\s*', '', sql, flags=re.IGNORECASE)
    return sql.strip()

# ===== KONFIGURACJA AGENTÓW =====

def create_improved_agent(llm, tools, system_message: str):
    """Tworzy agenta z ulepszonym promptem"""
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_message),
        MessagesPlaceholder(variable_name="messages"),
    ])
    
    if tools:
        return prompt | llm.bind_tools(tools)
    return prompt | llm

# Tworzenie agentów
search_agent = create_improved_agent(llm, tools, SEARCH_PROMPT)
value_agent = create_improved_agent(llm, tools, VALUE_PROMPT)
natural_agent = create_improved_agent(llm, [], NATURAL_PROMPT)

# ===== BUDOWA GRAFU =====

workflow = StateGraph(ImprovedAgentState)

# Dodaj węzły
workflow.add_node("search", improved_search_node)
workflow.add_node("tools", ToolNode(tools))
workflow.add_node("natural", natural_response_node)
workflow.add_node("value", value_node)

# Ustaw przepływ
workflow.set_entry_point("search")
workflow.add_edge("search", "tools")
workflow.add_edge("tools", "natural")

# Warunkowa krawędź - czy potrzebna analiza kosztów?
def should_calculate_cost(state) -> Literal["value", "end"]:
    context = state.get("context", {})
    last_message = state["messages"][-1].content.lower()
    
    if context.get("has_cost_query") or context.get("has_time_query"):
        return "value"
    return "end"

workflow.add_conditional_edges(
    "natural",
    should_calculate_cost,
    {
        "value": "value",
        "end": END
    }
)

workflow.add_edge("value", END)

# Kompiluj graf
graph = workflow.compile()

# ===== FUNKCJE POMOCNICZE =====

def run_query(question: str):
    """Uruchamia zapytanie i zwraca sformatowaną odpowiedź"""
    print(f"\n{'='*60}")
    print(f"PYTANIE: {question}")
    print(f"{'='*60}")
    
    input_data = {
        "messages": [HumanMessage(content=question)],
        "no_of_iterations": 0,
        "sql_query": "",
        "raw_data": "",
        "context": {}
    }
    
    # Zbierz wszystkie kroki
    steps = []
    for event in graph.stream(input_data, stream_mode="values"):
        steps.append(event)
    
    # Wyciągnij końcową odpowiedź
    final_messages = steps[-1]["messages"]
    
    # Formatuj odpowiedź
    response = {
        "question": question,
        "sql_query": steps[-1].get("sql_query", ""),
        "answer": final_messages[-1].content if final_messages else "Brak odpowiedzi",
        "steps": len(steps),
        "context": steps[-1].get("context", {})
    }
    
    return response

# ===== PRZYKŁADY UŻYCIA =====

if __name__ == "__main__":
    # Przykładowe zapytania
    test_queries = [
        "Ile czasu Dawid spędził na Facebooku w tym tygodniu?",
        "Kto najwięcej gra w godzinach pracy? Pokaż top 5 osób",
        "Ile pieniędzy straciliśmy na social media wczoraj?",
        "Pokaż mi aktywność użytkownika o MAC 1e:ea:73:e5:55:b0",
        "Jaka jest produktywność zespołu w tym miesiącu?",
    ]
    
    for query in test_queries:
        result = run_query(query)
        print(f"\nODPOWIEDŹ:\n{result['answer']}\n")
        if result['sql_query']:
            print(f"SQL: {result['sql_query']}\n")