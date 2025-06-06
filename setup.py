"""
Skrypt instalacyjny dla Multi-Agent System
"""
import os
import subprocess
import sys


def check_python_version():
    """Sprawdź wersję Pythona"""
    if sys.version_info < (3, 8):
        print("❌ Wymagany Python 3.8 lub nowszy!")
        sys.exit(1)
    print(f"✅ Python {sys.version.split()[0]}")


def create_directories():
    """Utwórz strukturę katalogów"""
    directories = [
        "agents",
        "core", 
        "config",
        "tools",
        "utils"
    ]
    
    for directory in directories:
        if not os.path.exists(directory):
            os.makedirs(directory)
            print(f"📁 Utworzono katalog: {directory}")
        else:
            print(f"✅ Katalog istnieje: {directory}")


def install_dependencies():
    """Zainstaluj zależności"""
    print("\n📦 Instaluję zależności...")
    try:
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "-r", "requirements.txt"
        ])
        print("✅ Zależności zainstalowane!")
    except subprocess.CalledProcessError:
        print("❌ Błąd podczas instalacji zależności!")
        sys.exit(1)


def create_env_file():
    """Utwórz przykładowy plik .env"""
    if not os.path.exists(".env"):
        with open(".env", "w") as f:
            f.write("# Konfiguracja Multi-Agent System\n")
            f.write("OPENAI_API_KEY_TEG=sk-your-api-key-here\n")
        print("📄 Utworzono plik .env - uzupełnij klucz API!")
    else:
        print("✅ Plik .env już istnieje")


def check_database():
    """Sprawdź dostępność bazy danych"""
    db_found = False
    for path in ["logs.db", "parser/logs.db", "../parser/logs.db"]:
        if os.path.exists(path):
            print(f"✅ Znaleziono bazę danych: {path}")
            db_found = True
            break
    
    if not db_found:
        print("⚠️  Nie znaleziono bazy danych!")
        print("   Umieść plik logs.db w głównym katalogu")
        print("   lub plik CSV z logami (nazwa musi zawierać 'logi')")


def main():
    """Główna funkcja setup"""
    print("🚀 Setup Multi-Agent System\n")
    
    # Sprawdzenia
    check_python_version()
    create_directories()
    install_dependencies()
    create_env_file()
    check_database()
    
    print("\n✅ Setup zakończony!")
    print("\n📝 Następne kroki:")
    print("1. Uzupełnij klucz API w pliku .env")
    print("2. Upewnij się, że masz bazę danych logs.db")
    print("3. Uruchom: streamlit run multi_agent_ui.py")


if __name__ == "__main__":
    main()