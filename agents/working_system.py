# agents/fixed_working_system.py
# System z poprawioną konwersją duration (milisekundy -> sekundy)

import os
import re
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage
from dotenv import load_dotenv

load_dotenv()

# ===== KONFIGURACJA =====
class Config:
    DB_PATH = r"C:\PJATK\SEMESTR2\teg projekt\projekt\Logi-projektTEG\parser\logs.db"
    TABLE_NAME = "logs"
    DEFAULT_HOURLY_RATE = 150  # PLN/h
    GOLD_PRICE_PLN = 280
    BTC_PRICE_PLN = 180000
    USD_RATE = 4.05
    EUR_RATE = 4.30
    # WAŻNE: duration jest w milisekundach!
    DURATION_UNIT = "milliseconds"

# ===== INICJALIZACJA =====
llm = ChatOpenAI(
    model_name="gpt-4o-mini",
    openai_api_key=os.environ['OPENAI_API_KEY_TEG'],
    temperature=0,
)

# ===== FUNKCJE POMOCNICZE =====

def check_duration_unit():
    """Sprawdza jednostkę duration analizując dane"""
    conn = sqlite3.connect(Config.DB_PATH)
    
    # Sprawdź maksymalną wartość duration
    query = """
    SELECT 
        MAX(duration) as max_duration,
        AVG(duration) as avg_duration,
        MIN(duration) as min_duration,
        COUNT(*) as count
    FROM logs
    WHERE duration > 0
    """
    
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    max_val = df['max_duration'].iloc[0]
    avg_val = df['avg_duration'].iloc[0]
    
    print(f"\n🔍 Analiza jednostki duration:")
    print(f"Max: {max_val:,.0f}")
    print(f"Avg: {avg_val:,.0f}")
    print(f"Min: {df['min_duration'].iloc[0]:,.0f}")
    
    # Jeśli średnia > 1000, to prawdopodobnie milisekundy
    if avg_val > 1000:
        print("✅ Duration jest prawdopodobnie w MILISEKUNDACH")
        return "milliseconds"
    else:
        print("✅ Duration jest prawdopodobnie w SEKUNDACH")
        return "seconds"

def duration_to_seconds(duration_value):
    """Konwertuje duration na sekundy w zależności od jednostki"""
    if Config.DURATION_UNIT == "milliseconds":
        return duration_value / 1000.0
    return duration_value

def execute_sql_query(query: str) -> pd.DataFrame:
    """Wykonuje zapytanie SQL i zwraca DataFrame"""
    print(f"\n[SQL] Wykonuję zapytanie:\n{query}")
    
    try:
        conn = sqlite3.connect(Config.DB_PATH)
        df = pd.read_sql_query(query, conn)
        conn.close()
        print(f"[SQL] Znaleziono {len(df)} rekordów")
        return df
    except Exception as e:
        print(f"[SQL] Błąd: {e}")
        return pd.DataFrame()

def calculate_loss(seconds: float) -> Dict:
    """Oblicza straty finansowe na podstawie sekund"""
    hours = seconds / 3600
    pln_loss = hours * Config.DEFAULT_HOURLY_RATE
    
    return {
        "hours": round(hours, 2),
        "minutes": round((seconds % 3600) / 60, 0),
        "pln": round(pln_loss, 2),
        "usd": round(pln_loss / Config.USD_RATE, 2),
        "eur": round(pln_loss / Config.EUR_RATE, 2),
        "gold_grams": round(pln_loss / Config.GOLD_PRICE_PLN, 3),
        "btc": round(pln_loss / Config.BTC_PRICE_PLN, 6),
        "coffee_cups": round(pln_loss / 15, 0),
        "netflix_months": round(pln_loss / 60, 1),
    }

# ===== PROMPTY Z UWZGLĘDNIENIEM MILISEKUND =====

SQL_PROMPT = f"""Jesteś ekspertem SQL dla bazy SQLite. Konwertujesz pytania na zapytania SQL.

NAZWA TABELI: logs

STRUKTURA:
- date (DATE): data w formacie YYYY-MM-DD
- time (TIME): czas w formacie HH:MM:SS
- srcname (TEXT): nazwa użytkownika (np. "Dawid-s-S23", "iPhone")
- app (TEXT): nazwa aplikacji (np. "Facebook", "Instagram", "YouTube")
- appcat (TEXT): kategoria (Social.Media, Game, Video/Audio)
- duration (INTEGER): czas w MILISEKUNDACH (dziel przez 1000 dla sekund!)
- sentbyte, rcvdbyte: transfer danych

WAŻNE: duration jest w MILISEKUNDACH!
- Dla sekund: duration/1000.0
- Dla minut: duration/1000.0/60
- Dla godzin: duration/1000.0/3600

PRZYKŁADY:
- "ile czasu na Facebook" → SELECT srcname, SUM(duration)/1000.0 as seconds, SUM(duration)/1000.0/3600 as hours FROM logs WHERE app LIKE '%Facebook%' GROUP BY srcname
- "kto najwięcej gra" → SELECT srcname, SUM(duration)/1000.0/3600 as hours FROM logs WHERE appcat = 'Game' GROUP BY srcname ORDER BY hours DESC
- "czas na social media dzisiaj" → SELECT app, SUM(duration)/1000.0/3600 as hours FROM logs WHERE appcat = 'Social.Media' AND date = date('now') GROUP BY app

Zawsze używaj duration/1000.0 aby otrzymać sekundy!
Zwróć TYLKO zapytanie SQL."""

REPORT_PROMPT = """Jesteś asystentem analizującym ruch sieciowy w firmie.

ZADANIE: Przekształć dane SQL w czytelny raport po polsku.

ZASADY:
1. Wartości 'seconds' to rzeczywiste sekundy
2. Wartości 'hours' to rzeczywiste godziny
3. Używaj realistycznych opisów (np. "2.5 godziny", nie "248 godzin")
4. Dodaj emoji: �� (social), 🎮 (gry), 💼 (praca)
5. Sprawdź czy wyniki są realistyczne (max kilka godzin dziennie)

Jeśli widzisz nierealistyczne wartości (np. 248 godzin), zgłoś to jako błąd."""

# ===== GŁÓWNE FUNKCJE =====

def generate_sql_query(question: str) -> str:
    """Generuje zapytanie SQL na podstawie pytania"""
    messages = [
        {"role": "system", "content": SQL_PROMPT},
        {"role": "user", "content": question}
    ]
    
    response = llm.invoke(messages)
    sql = response.content.strip()
    
    # Wyczyść SQL
    sql = re.sub(r'```sql\s*', '', sql)
    sql = re.sub(r'```\s*', '', sql)
    
    return sql.strip()

def generate_report(df: pd.DataFrame, question: str, sql_query: str) -> str:
    """Generuje raport na podstawie danych"""
    if df.empty:
        return f"""📊 **Analiza: {question}**

❌ Nie znaleziono danych spełniających kryteria.

💡 Spróbuj bardziej ogólnego zapytania."""

    # Konwertuj duration na sekundy jeśli jest w milisekundach
    if 'duration' in df.columns:
        df['duration_seconds'] = df['duration'] / 1000.0
        df['duration_hours'] = df['duration_seconds'] / 3600
    
    # Przygotuj dane do raportu
    data_summary = f"Znaleziono {len(df)} wyników.\n\n"
    
    if len(df) <= 10:
        # Pokaż tylko istotne kolumny
        display_cols = [col for col in df.columns if col not in ['duration']]
        data_summary += df[display_cols].to_string(index=False)
    else:
        data_summary += df.head(10).to_string(index=False)
        data_summary += f"\n... i {len(df) - 10} więcej"
    
    messages = [
        {"role": "system", "content": REPORT_PROMPT},
        {"role": "user", "content": f"Pytanie: {question}\n\nDane:\n{data_summary}"}
    ]
    
    response = llm.invoke(messages)
    return response.content

def analyze_query(question: str) -> Dict:
    """Główna funkcja analizująca pytanie"""
    print(f"\n{'='*60}")
    print(f"📝 PYTANIE: {question}")
    print(f"{'='*60}")
    
    try:
        # 1. Generuj SQL
        sql_query = generate_sql_query(question)
        print(f"\n[SQL]:\n{sql_query}")
        
        # 2. Wykonaj zapytanie
        df = execute_sql_query(sql_query)
        
        # 3. Generuj raport
        report = generate_report(df, question, sql_query)
        
        # 4. Dodaj analizę kosztów jeśli pytanie o pieniądze/czas
        if any(word in question.lower() for word in ['koszt', 'stracił', 'pieniądze', 'złoto', 'btc', 'czas']):
            if not df.empty:
                # Szukaj kolumny z czasem w sekundach
                time_column = None
                for col in ['seconds', 'total_seconds', 'duration_seconds']:
                    if col in df.columns:
                        time_column = col
                        break
                
                if time_column:
                    total_seconds = df[time_column].sum()
                    if total_seconds > 0 and total_seconds < 1000000:  # Sanity check
                        losses = calculate_loss(float(total_seconds))
                        
                        cost_report = f"""\n\n💸 **Analiza finansowa:**

⏱️ Czas: **{losses['hours']} godzin {losses['minutes']} minut**
💰 Koszt: **{losses['pln']} PLN**

Inne waluty:
- 💵 {losses['usd']} USD
- 💶 {losses['eur']} EUR
- 🥇 {losses['gold_grams']} gramów złota
- ₿ {losses['btc']} BTC

Porównania:
- ☕ {int(losses['coffee_cups'])} kaw
- 📺 {losses['netflix_months']} miesięcy Netflix"""
                        
                        report += cost_report
        
        return {
            "question": question,
            "sql_query": sql_query,
            "data": df.to_dict('records') if not df.empty else [],
            "report": report,
            "success": True
        }
        
    except Exception as e:
        return {
            "question": question,
            "sql_query": "",
            "data": [],
            "report": f"❌ Błąd: {str(e)}",
            "success": False
        }

# ===== FUNKCJE TESTOWE =====

def check_database_stats():
    """Sprawdza podstawowe statystyki bazy"""
    print("\n�� STATYSTYKI BAZY DANYCH\n")
    
    # Najpierw sprawdź jednostkę duration
    Config.DURATION_UNIT = check_duration_unit()
    
    stats_queries = {
        "Całkowita liczba rekordów": "SELECT COUNT(*) as count FROM logs",
        "Liczba użytkowników": "SELECT COUNT(DISTINCT srcname) as users FROM logs",
        "Kategorie aplikacji": "SELECT appcat, COUNT(*) as count FROM logs WHERE appcat IS NOT NULL GROUP BY appcat",
        "Top 10 aplikacji (w godzinach)": """
            SELECT app, 
                   COUNT(*) as sessions, 
                   SUM(duration)/1000.0/3600.0 as hours 
            FROM logs 
            GROUP BY app 
            ORDER BY hours DESC 
            LIMIT 10
        """,
        "Zakres dat": "SELECT MIN(date) as od, MAX(date) as do FROM logs",
    }
    
    for name, query in stats_queries.items():
        df = execute_sql_query(query)
        print(f"\n{name}:")
        print(df.to_string(index=False))

def run_analysis_examples():
    """Uruchamia przykładowe analizy z poprawnymi jednostkami"""
    print("\n🎯 PRZYKŁADOWE ANALIZY (z poprawioną konwersją czasu)\n")
    
    examples = [
        "Ile czasu spędzono na Facebooku?",
        "Pokaż top 5 użytkowników pod względem czasu online 16/05/24"
    ]
    
    for question in examples:
        result = analyze_query(question)
        print(f"\n{'='*60}")
        print(f"❓ {question}")
        print(f"{'='*60}")
        print(result['report'])

# ===== MAIN =====

if __name__ == "__main__":
    # Sprawdź statystyki
    check_database_stats()
    
    # Uruchom przykłady
    run_analysis_examples()
    
    # Tryb interaktywny
    print("\n\n🤖 TRYB INTERAKTYWNY")
    print("Wpisz 'exit' aby zakończyć\n")
    
    while True:
        question = input("\n❓ Twoje pytanie: ")
        if question.lower() in ['exit', 'quit', 'q']:
            break
            
        result = analyze_query(question)
        print("\n" + result['report'])
