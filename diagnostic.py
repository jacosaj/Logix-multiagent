"""
Skrypt diagnostyczny dla Multi-Agent System
Sprawdza czy wszystko jest poprawnie skonfigurowane
"""
import os
import sqlite3
import sys


def check_database():
    """Sprawdź bazę danych i jej zawartość"""
    print("\n🔍 Sprawdzam bazę danych...")
    
    # Znajdź bazę
    db_found = False
    db_path = None
    
    possible_paths = ["./logs.db", "./parser/logs.db", "../parser/logs.db", "logs.db"]
    for path in possible_paths:
        if os.path.exists(path):
            db_path = path
            db_found = True
            break
    
    if not db_found:
        print("❌ Nie znaleziono bazy danych logs.db!")
        print("   Umieść plik w głównym katalogu projektu")
        return False
    
    print(f"✅ Znaleziono bazę: {db_path}")
    
    # Sprawdź zawartość
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Sprawdź strukturę
        cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='logs'")
        table_schema = cursor.fetchone()
        
        if not table_schema:
            print("❌ Brak tabeli 'logs' w bazie!")
            return False
        
        print("✅ Tabela 'logs' istnieje")
        print(f"   Schemat: {table_schema[0][:100]}...")
        
        # Sprawdź dane
        cursor.execute("SELECT COUNT(*) FROM logs")
        count = cursor.fetchone()[0]
        print(f"✅ Liczba rekordów: {count}")
        
        if count == 0:
            print("⚠️  UWAGA: Tabela jest pusta!")
            return False
        
        # Pokaż przykładowe dane
        cursor.execute("SELECT * FROM logs LIMIT 3")
        columns = [desc[0] for desc in cursor.description]
        print(f"✅ Kolumny: {columns}")
        
        print("\n📊 Przykładowe dane:")
        for row in cursor.fetchall():
            print(f"   {row}")
        
        # Statystyki
        print("\n📈 Statystyki:")
        cursor.execute("SELECT COUNT(DISTINCT srcname) as users, COUNT(DISTINCT app) as apps FROM logs")
        stats = cursor.fetchone()
        print(f"   Użytkownicy: {stats[0]}")
        print(f"   Aplikacje: {stats[1]}")
        
        # TOP aplikacje
        cursor.execute("""
            SELECT app, COUNT(*) as count, SUM(duration) as total_duration 
            FROM logs 
            GROUP BY app 
            ORDER BY total_duration DESC 
            LIMIT 5
        """)
        print("\n🏆 TOP 5 aplikacji:")
        for app in cursor.fetchall():
            print(f"   {app[0]}: {app[1]} sesji, {app[2]} sekund")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Błąd podczas sprawdzania bazy: {e}")
        return False


def check_env():
    """Sprawdź zmienne środowiskowe"""
    print("\n🔍 Sprawdzam konfigurację...")
    
    if not os.path.exists(".env"):
        print("❌ Brak pliku .env!")
        return False
    
    print("✅ Plik .env istnieje")
    
    # Sprawdź klucz API
    from dotenv import load_dotenv
    load_dotenv()
    
    api_key = os.environ.get('OPENAI_API_KEY_TEG')
    if not api_key or api_key == "sk-your-api-key-here":
        print("❌ Brak prawidłowego klucza API w .env!")
        print("   Ustaw OPENAI_API_KEY_TEG=sk-...")
        return False
    
    print("✅ Klucz API skonfigurowany")
    return True


def test_agents():
    """Testuj agentów"""
    print("\n🧪 Testuję agentów...")
    
    try:
        from langgraph_multi_agent import MultiAgentSystem
        
        print("✅ Import systemu działa")
        
        # Spróbuj utworzyć system
        system = MultiAgentSystem()
        print("✅ System utworzony pomyślnie")
        
        # Testowe zapytanie
        test_query = "Pokaż mi 5 najczęściej używanych aplikacji"
        print(f"\n📝 Testowe zapytanie: {test_query}")
        
        result = system.process(test_query)
        
        if result:
            print("✅ System odpowiedział")
            # Pokaż fragment odpowiedzi
            messages = result.get("messages", [])
            if messages:
                last_msg = messages[-1].content if hasattr(messages[-1], 'content') else str(messages[-1])
                print(f"   Odpowiedź: {last_msg[:200]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Błąd podczas testowania: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Główna funkcja diagnostyczna"""
    print("🚀 Diagnostyka Multi-Agent System")
    print("=" * 50)
    
    checks = [
        ("Środowisko", check_env),
        ("Baza danych", check_database),
        ("Agenci", test_agents)
    ]
    
    results = []
    for name, check_func in checks:
        print(f"\n{'='*50}")
        result = check_func()
        results.append((name, result))
    
    # Podsumowanie
    print(f"\n{'='*50}")
    print("📊 PODSUMOWANIE:")
    print(f"{'='*50}")
    
    all_passed = True
    for name, result in results:
        status = "✅ OK" if result else "❌ BŁĄD"
        print(f"{name}: {status}")
        if not result:
            all_passed = False
    
    if all_passed:
        print("\n✅ Wszystko działa poprawnie!")
        print("   Możesz uruchomić: streamlit run multi_agent_ui.py")
    else:
        print("\n❌ Wykryto problemy - napraw je przed uruchomieniem")
    
    print(f"\n{'='*50}")


if __name__ == "__main__":
    main()