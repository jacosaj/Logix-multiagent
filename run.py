#!/usr/bin/env python
"""
Skrypt uruchamiający Multi-Agent System
"""
import os
import sys
import subprocess


def main():
    """Uruchom aplikację"""
    print("🚀 Uruchamiam Multi-Agent System...")
    
    # Sprawdź czy istnieje plik .env
    if not os.path.exists(".env"):
        print("⚠️  Brak pliku .env!")
        print("   Uruchom najpierw: python setup.py")
        return
    
    # Sprawdź czy są zainstalowane zależności
    try:
        import streamlit
        import langchain
        import langgraph
    except ImportError:
        print("⚠️  Brak wymaganych pakietów!")
        print("   Uruchom: pip install -r requirements.txt")
        return
    
    # Uruchom Streamlit
    try:
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", 
            "multi_agent_ui.py",
            "--server.port", "8502",
            "--server.address", "localhost"
        ])
    except KeyboardInterrupt:
        print("\n👋 Do zobaczenia!")
    except Exception as e:
        print(f"❌ Błąd: {e}")


if __name__ == "__main__":
    main()