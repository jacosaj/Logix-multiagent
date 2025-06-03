# agents/working_system.py
# System dostosowany do Twojej bazy danych

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
    DB_PATH = "./parser/logs.db"  # Twoja ścieżka
    TABLE_NAME = "logs"
    DEFAULT_HOURLY_RATE = 150  # PLN/h
    GOLD_PRICE_PLN = 280
    BTC_PRICE_PLN = 180000
    USD_RATE = 4.05
    EUR_RATE = 4.30

# ===== INICJALIZACJA =====
llm = ChatOpenAI(
    model_name="gpt-4o-mini",
    openai_api_key=os.environ['OPENAI_API_KEY_TEG'],
    temperature=0,
)

# ===== FUNKCJE POMOCNICZE =====

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
    """Oblicza straty finansowe"""
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

# ===== PROMPTY DOSTOSOWANE DO TWOICH DANYCH =====

SQL_PROMPT = """Jesteś ekspertem SQL dla bazy SQLite. Konwertujesz pytania na zapytania SQL.

NAZWA TABELI: logs

STRUKTURA:
- date (DATE): data w formacie YYYY-MM-DD
- time (TIME): czas w formacie HH:MM:SS
- srcname (TEXT): nazwa użytkownika (np. "Dawid-s-S23", "iPhone")
- app (TEXT): nazwa aplikacji (np. "Facebook", "Instagram", "YouTube")
- appcat (TEXT): kategoria (Social.Media, Game, Adult, Business, Development)
- duration (INTEGER): czas w SEKUNDACH
- sentbyte, rcvdbyte: transfer danych
- srcip, mastersrcmac: dane techniczne

PRZYKŁADOWE DANE:
- Użytkownicy: Dawid-s-S23, iPhone, Galaxy-S21, MacBook-Pro
- Aplikacje: Facebook, Instagram, YouTube, Netflix, Steam
- Kategorie: Social.Media, Game, Adult

ZASADY SQL:
1. Używaj date('now') dla bieżącej daty
2. Dla okresów: date('now', '-7 days'), date('now', '-1 day')
3. Wyszukiwanie: WHERE srcname LIKE '%Dawid%'
4. Zawsze używaj SUM(duration) dla czasu
5. Pamiętaj o GROUP BY przy agregacji

PRZYKŁADY:
- "ile czasu na Facebook" → SELECT srcname, SUM(duration) as total_seconds FROM logs WHERE app LIKE '%Facebook%' GROUP BY srcname
- "kto najwięcej gra" → SELECT srcname, SUM(duration) as total_seconds FROM logs WHERE appcat = 'Game' GROUP BY srcname ORDER BY total_seconds DESC
- "social media dzisiaj" → SELECT app, SUM(duration) as total_seconds FROM logs WHERE appcat = 'Social.Media' AND date = date('now') GROUP BY app

Zwróć TYLKO zapytanie SQL, bez komentarzy."""

REPORT_PROMPT = """Jesteś asystentem analizującym ruch sieciowy w firmie.

ZADANIE: Przekształć dane SQL w czytelny raport po polsku.

ZASADY:
1. Konwertuj sekundy na godziny i minuty (3600s = 1h)
2. Używaj emotikonów: 📱 (social), 🎮 (gry), 💼 (praca)
3. Wyróżnij najważniejsze dane pogrubieniem
4. Dodaj kontekst (np. "to 20% dnia pracy")
5. Bądź konkretny - podawaj nazwy użytkowników i aplikacji

FORMAT:
- Nagłówek z emoji
- Podsumowanie główne
- Lista szczegółów
- Wniosek/rekomendacja

Jeśli brak danych, napisz jasno dlaczego."""

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
    sql = re.sub(r'SQLQuery:\s*', '', sql, flags=re.IGNORECASE)
    
    return sql.strip()

def generate_report(df: pd.DataFrame, question: str, sql_query: str) -> str:
    """Generuje raport na podstawie danych"""
    if df.empty:
        return f"""📊 **Analiza: {question}**

❌ Nie znaleziono danych spełniających kryteria.

Możliwe przyczyny:
- Brak aktywności w wybranym okresie
- Niepoprawna nazwa użytkownika/aplikacji
- Dane jeszcze nie zostały zaimportowane

💡 Spróbuj bardziej ogólnego zapytania."""

    # Przygotuj dane do raportu
    data_summary = f"Znaleziono {len(df)} wyników.\n\n"
    
    if len(df) <= 10:
        data_summary += df.to_string(index=False)
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
                # Szukaj kolumny z czasem
                time_column = None
                for col in ['total_seconds', 'duration', 'time_sum']:
                    if col in df.columns:
                        time_column = col
                        break
                
                if time_column:
                    total_seconds = df[time_column].sum() if len(df) > 1 else df[time_column].iloc[0]
                    if total_seconds > 0:
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
- 📺 {losses['netflix_months']} miesięcy Netflix
- 💸 {int(losses['pln']/500)} banknotów 500 zł"""
                        
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

def run_analysis_examples():
    """Uruchamia przykładowe analizy"""
    
    print("\n🎯 PRZYKŁADOWE ANALIZY\n")
    
    examples = [
        "Ile czasu spędzono na Facebooku?",
        "Kto najwięcej używał social media?",
        "Jakie aplikacje z kategorii Game były używane?",
        "Ile kosztowało nas YouTube w godzinach pracy?",
        "Pokaż top 5 użytkowników pod względem czasu online",
        "Ile czasu stracił Dawid na social media?",
    ]
    
    for question in examples:
        result = analyze_query(question)
        print(f"\n{'='*60}")
        print(f"❓ {question}")
        print(f"{'='*60}")
        print(result['report'])
        if result['success'] and result['data']:
            print(f"\n📊 Znaleziono {len(result['data'])} rekordów")

def check_database_stats():
    """Sprawdza podstawowe statystyki bazy"""
    print("\n📊 STATYSTYKI BAZY DANYCH\n")
    
    stats_queries = {
        "Całkowita liczba rekordów": "SELECT COUNT(*) as count FROM logs",
        "Liczba użytkowników": "SELECT COUNT(DISTINCT srcname) as count FROM logs",
        "Kategorie aplikacji": "SELECT appcat, COUNT(*) as count FROM logs WHERE appcat IS NOT NULL GROUP BY appcat",
        "Top 10 aplikacji": "SELECT app, COUNT(*) as sessions, SUM(duration)/3600.0 as hours FROM logs GROUP BY app ORDER BY hours DESC LIMIT 10",
        "Zakres dat": "SELECT MIN(date) as od, MAX(date) as do FROM logs",
    }
    
    for name, query in stats_queries.items():
        df = execute_sql_query(query)
        print(f"\n{name}:")
        print(df.to_string(index=False))

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
