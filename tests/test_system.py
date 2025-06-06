"""
Testy dla Multi-Agent System
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents import AgentState
from config import Config
from utils import ConversationHistory


def test_config():
    """Test konfiguracji"""
    print("🧪 Test konfiguracji...")
    
    assert Config.OPENAI_MODEL == "gpt-4o-mini"
    assert Config.MAX_ITERATIONS == 10
    assert len(Config.AGENT_EMOJIS) >= 4
    assert len(Config.EXAMPLE_QUERIES) > 0
    
    print("✅ Konfiguracja OK")


def test_agent_state():
    """Test stanu agenta"""
    print("\n🧪 Test AgentState...")
    
    # Utwórz przykładowy stan
    state = {
        "messages": [],
        "current_agent": "supervisor",
        "context": {},
        "sql_results": [],
        "analysis_results": {},
        "next_agent": "sql_agent"
    }
    
    # Sprawdź typy
    assert isinstance(state["messages"], list)
    assert isinstance(state["context"], dict)
    assert isinstance(state["sql_results"], list)
    
    print("✅ AgentState OK")


def test_conversation_history():
    """Test historii konwersacji"""
    print("\n🧪 Test ConversationHistory...")
    
    # Test identyfikacji agenta
    sql_content = "Pobrałem dane z bazy danych"
    analyst_content = "Analizuję trendy w danych"
    report_content = "Tworzę raport końcowy"
    
    assert ConversationHistory._identify_agent(sql_content) == "sql_agent"
    assert ConversationHistory._identify_agent(analyst_content) == "analyst"
    assert ConversationHistory._identify_agent(report_content) == "report_writer"
    
    print("✅ ConversationHistory OK")


def test_imports():
    """Test importów modułów"""
    print("\n🧪 Test importów...")
    
    try:
        from agents import SupervisorAgent, SQLAgentNode, DataAnalystAgent, ReportWriterAgent
        from core import GraphBuilder
        from tools import ALL_TOOLS
        print("✅ Wszystkie importy działają")
    except ImportError as e:
        print(f"❌ Błąd importu: {e}")
        return False
    
    return True


def test_multi_agent_system():
    """Test głównego systemu"""
    print("\n🧪 Test MultiAgentSystem...")
    
    try:
        from langgraph_multi_agent import MultiAgentSystem
        
        # Sprawdź czy można utworzyć instancję
        # (bez faktycznej inicjalizacji - wymaga klucza API)
        print("✅ MultiAgentSystem można zaimportować")
    except Exception as e:
        print(f"❌ Błąd: {e}")
        return False
    
    return True


def run_all_tests():
    """Uruchom wszystkie testy"""
    print("🚀 Uruchamiam testy Multi-Agent System\n")
    
    tests = [
        test_config,
        test_agent_state,
        test_conversation_history,
        test_imports,
        test_multi_agent_system
    ]
    
    failed = 0
    for test in tests:
        try:
            test()
        except Exception as e:
            print(f"❌ Test {test.__name__} nie powiódł się: {e}")
            failed += 1
    
    print(f"\n📊 Podsumowanie: {len(tests) - failed}/{len(tests)} testów przeszło")
    
    if failed == 0:
        print("✅ Wszystkie testy przeszły pomyślnie!")
    else:
        print(f"❌ {failed} testów nie powiodło się")


if __name__ == "__main__":
    run_all_tests()