# Uproszczona implementacja bez tool calls
# Plik: agents/simple_system.py

import os
import re
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage, AIMessage
from dotenv import load_dotenv

load_dotenv()

# ===== KONFIGURACJA =====
class Config:
    DB_PATH = r"./parser/logs.db"  # Zmień na swoją ścieżkę
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

def calculate_loss(seconds: int) -> Dict:
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
    }

def format_seconds_to_time(seconds: int) -> str:
    """Formatuje sekundy na czytelny czas"""
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    
    if hours > 0:
        return f"{hours} godzin {minutes} minut"
    elif minutes > 0:
        return f"{minutes} minut"
    else:
        return f"{seconds} sekund"

# ===== PROMPTY =====

SQL_PROMPT = """Jesteś ekspertem SQL dla bazy SQLite. Konwertujesz pytania na zapytania SQL.

STRUKTURA TABELI logs:
- date (TEXT format: YYYY-MM-DD)
- time (TEXT format: HH:MM:SS)
- srcname (TEXT): nazwa użytkownika
- srcip (TEXT): IP źródłowe
- mastersrcmac (TEXT): adres MAC
- app (TEXT): nazwa aplikacji
- appcat (TEXT): kategoria (Social.Media, Game, Adult, Business, Development)
- duration (INTEGER): czas w SEKUNDACH
- action (TEXT): typ akcji

WAŻNE dla SQLite:
- Używaj date('now') dla bieżącej daty
- Dla wczoraj: date('now', '-1 day')
- Dla tygodnia: date('now', '-7 days')
- NIE używaj CURDATE(), INTERVAL - to MySQL!

PRZYKŁADY:
- "wczoraj" → WHERE date = date('now', '-1 day')
- "w tym tygodniu" → WHERE date >= date('now', '-7 days')
- "Dawid" → WHERE srcname LIKE '%Dawid%'

Zwróć TYLKO zapytanie SQL."""

REPORT_PROMPT = """Jesteś asystentem analizującym dane o ruchu sieciowym.

Otrzymujesz dane w formacie DataFrame i tworzysz przyjazny raport po polsku.

ZASADY:
1. Konwertuj sekundy na godziny i minuty
2. Używaj emotikonów dla lepszej czytelności
3. Grupuj podobne dane
4. Podkreśl najważniejsze informacje
5. Jeśli brak danych, napisz to jasno

Bądź konkretny i pomocny."""

# ===== GŁÓWNE FUNKCJE =====

def generate_sql_query(question: str) -> str:
    """Generuje zapytanie SQL na podstawie pytania"""
    prompt = ChatPromptTemplate.from_template(SQL_PROMPT)
    
    messages = prompt.format_messages()
    messages.append(HumanMessage(content=question))
    
    response = llm.invoke(messages)
    
    # Wyczyść odpowiedź
    sql = response.content.strip()
    sql = re.sub(r'```sql\s*', '', sql)
    sql = re.sub(r'```\s*', '', sql)
    sql = re.sub(r'SQLQuery:\s*', '', sql, flags=re.IGNORECASE)
    
    return sql.strip()

def generate_report(df: pd.DataFrame, question: str) -> str:
    """Generuje raport na podstawie danych"""
    prompt = ChatPromptTemplate.from_template(REPORT_PROMPT)
    
    # Przygotuj opis danych
    if df.empty:
        data_description = "Brak danych spełniających kryteria."
    else:
        data_description = f"Znaleziono {len(df)} rekordów.\n\n"
        
        # Pokaż pierwsze kilka rekordów
        if len(df) <= 10:
            data_description += df.to_string()
        else:
            data_description += df.head(10).to_string()
            data_description += f"\n... i {len(df) - 10} więcej rekordów"
    
    messages = prompt.format_messages()
    messages.append(HumanMessage(content=f"Pytanie: {question}\n\nDane:\n{data_description}"))
    
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
        print(f"\n[GENERATED SQL]:\n{sql_query}")
        
        # 2. Wykonaj zapytanie
        df = execute_sql_query(sql_query)
        
        # 3. Generuj raport
        report = generate_report(df, question)
        
        # 4. Sprawdź czy pytanie dotyczy kosztów
        if any(word in question.lower() for word in ['koszt', 'stracił', 'pieniądze', 'złoto', 'btc']):
            # Oblicz całkowity czas
            if not df.empty and 'total_seconds' in df.columns:
                total_seconds = df['total_seconds'].sum()
            elif not df.empty and 'duration' in df.columns:
                total_seconds = df['duration'].sum()
            else:
                total_seconds = 0
            
            if total_seconds > 0:
                losses = calculate_loss(int(total_seconds))
                cost_report = f"\n\n💸 **Analiza finansowa:**\n"
                cost_report += f"- Czas: {losses['hours']} godzin {losses['minutes']} minut\n"
                cost_report += f"- Koszt: **{losses['pln']} PLN**\n"
                cost_report += f"- To równowartość: {losses['usd']} USD, {losses['eur']} EUR\n"
                cost_report += f"- Lub: {losses['gold_grams']} gramów złota, {losses['btc']} BTC\n"
                cost_report += f"- Można by za to kupić {int(losses['coffee_cups'])} kaw ☕"
                
                report += cost_report
        
        return {
            "question": question,
            "sql_query": sql_query,
            "data": df,
            "report": report,
            "success": True
        }
        
    except Exception as e:
        return {
            "question": question,
            "sql_query": "",
            "data": pd.DataFrame(),
            "report": f"❌ Wystąpił błąd: {str(e)}",
            "success": False
        }

# ===== PRZYKŁADY UŻYCIA =====

def test_system():
    """Testuje system z przykładowymi zapytaniami"""
    
    # Najpierw sprawdźmy co mamy w bazie
    print("\n🔍 Sprawdzam zawartość bazy danych...")
    
    check_queries = [
        "SELECT COUNT(*) as total FROM logs",
        "SELECT DISTINCT srcname FROM logs LIMIT 10",
        "SELECT DISTINCT app FROM logs WHERE app LIKE '%Facebook%' LIMIT 5",
        "SELECT DISTINCT appcat FROM logs",
        "SELECT MIN(date) as oldest, MAX(date) as newest FROM logs"
    ]
    
    for query in check_queries:
        df = execute_sql_query(query)
        if not df.empty:
            print(f"\n{query}")
            print(df)
    
    print("\n" + "="*60)
    print("🚀 TESTY SYSTEMU")
    print("="*60)
    
    test_queries = [
        "Ile czasu użytkownicy spędzili na Facebooku?",
        "Kto najwięcej używał aplikacji z kategorii Social.Media?",
        "Pokaż top 5 użytkowników pod względem czasu spędzonego w aplikacjach",
        "Ile czasu straciliśmy na grach w ostatnim tygodniu?",
        "Jaki był całkowity transfer danych dla użytkownika Dawid?",
    ]
    
    for query in test_queries:
        result = analyze_query(query)
        print(f"\n✅ ODPOWIEDŹ:")
        print(result['report'])
        print(f"\n📊 SQL: {result['sql_query']}")
        print("-" * 60)

if __name__ == "__main__":
    test_system()