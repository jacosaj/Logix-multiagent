"""
Data Analyst Agent - analizuje dane i tworzy wnioski
"""
from typing import Dict, Any, List
from datetime import datetime
import json
import re
from langchain_core.messages import AIMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI

from .state import AgentState


class DataAnalystAgent:
    """Agent analityka danych"""
    
    def __init__(self, llm: ChatOpenAI):
        self.llm = llm
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """Jesteś Data Analyst specjalizującym się w analizie logów sieciowych.

KONTEKST:
Analizujesz dane z logów sieciowych zawierające informacje o:
- Wykorzystaniu aplikacji przez użytkowników
- Czasie spędzonym w różnych aplikacjach
- Transferze danych (bytes_sent/received)
- Kategoriach aplikacji (social_media, business, browser, etc.)

TWOJE ZADANIA:
1. Przeanalizuj otrzymane dane SQL
2. Zidentyfikuj kluczowe trendy i wzorce:
   - Które aplikacje są najczęściej używane?
   - Którzy użytkownicy są najbardziej aktywni?
   - Jakie kategorie dominują?
   - Czy są nietypowe wzorce użycia?
3. Oblicz statystyki:
   - Średni czas użycia per aplikacja/użytkownik
   - Procentowy udział kategorii
   - TOP użytkownicy i aplikacje
4. Sformułuj wnioski biznesowe

Dane SQL do analizy:
{sql_results}

WAŻNE: 
- Bazuj TYLKO na rzeczywistych danych z SQL
- Nie wymyślaj liczb
- Jeśli dane są w formacie tekstowym, wyodrębnij z nich wartości liczbowe
"""),
            MessagesPlaceholder(variable_name="messages")
        ])
        
        self.chain = self.prompt | self.llm
    
    def _extract_data_from_sql_results(self, sql_results: List[Dict]) -> Dict[str, Any]:
        """Wyodrębnij dane z wyników SQL, obsługując różne formaty"""
        extracted_data = {
            "users": {},
            "apps": {},
            "categories": {},
            "total_records": 0,
            "has_data": False
        }
        
        if not sql_results:
            return extracted_data
        
        # Pobierz pierwszy (i zazwyczaj jedyny) wynik
        sql_result = sql_results[0] if sql_results else {}
        
        # Sprawdź czy mamy strukturyzowane dane
        if sql_result.get("data"):
            extracted_data["has_data"] = True
            data_list = sql_result["data"]
            
            for row in data_list:
                # Obsługa danych użytkowników (social media query)
                if "user" in row or "srcname" in row:
                    user_name = row.get("user") or row.get("srcname")
                    total_seconds = row.get("total_seconds", 0)
                    total_hours = row.get("total_hours", 0)
                    sessions = row.get("sessions", 0)
                    
                    extracted_data["users"][user_name] = {
                        "total_seconds": total_seconds,
                        "total_hours": total_hours,
                        "sessions": sessions
                    }
                
                # Obsługa danych aplikacji
                if "app" in row:
                    app_name = row["app"]
                    usage_count = row.get("usage_count", 0)
                    total_seconds = row.get("total_seconds", 0)
                    total_hours = row.get("total_hours", 0)
                    unique_users = row.get("unique_users", 0)
                    
                    extracted_data["apps"][app_name] = {
                        "usage_count": usage_count,
                        "total_seconds": total_seconds,
                        "total_hours": total_hours,
                        "unique_users": unique_users
                    }
            
            extracted_data["total_records"] = len(data_list)
        
        # Fallback: próbuj parsować tekst
        elif sql_result.get("result"):
            text = sql_result["result"]
            extracted_data["has_data"] = True
            
            # Szukaj wzorców użytkownik: czas
            user_pattern = r'([A-Za-z0-9\-]+)\s*\|\s*(\d+)\s*\|\s*([\d.]+)\s*\|\s*(\d+)'
            for match in re.finditer(user_pattern, text):
                user_name = match.group(1)
                total_seconds = int(match.group(2))
                total_hours = float(match.group(3))
                sessions = int(match.group(4))
                
                extracted_data["users"][user_name] = {
                    "total_seconds": total_seconds,
                    "total_hours": total_hours,
                    "sessions": sessions
                }
            
            # Liczba znalezionych rekordów
            count_match = re.search(r'Znaleziono (\d+) wyników', text)
            if count_match:
                extracted_data["total_records"] = int(count_match.group(1))
        
        return extracted_data
    
    def _analyze_social_media_usage(self, users_data: Dict) -> Dict[str, Any]:
        """Analizuj użycie social media"""
        if not users_data:
            return {}
        
        # Sortuj użytkowników po czasie
        sorted_users = sorted(
            users_data.items(), 
            key=lambda x: x[1].get("total_seconds", 0), 
            reverse=True
        )
        
        # TOP użytkownik
        if sorted_users:
            top_user = sorted_users[0]
            return {
                "top_user": {
                    "name": top_user[0],
                    "total_hours": top_user[1].get("total_hours", 0),
                    "total_seconds": top_user[1].get("total_seconds", 0),
                    "sessions": top_user[1].get("sessions", 0)
                },
                "top_5_users": [
                    {
                        "name": user[0],
                        "hours": user[1].get("total_hours", 0)
                    } for user in sorted_users[:5]
                ]
            }
        
        return {}
    
    def process(self, state: AgentState) -> Dict[str, Any]:
        """Przeanalizuj dane"""
        sql_results = state.get("sql_results", [])
        
        if not sql_results:
            return {
                "messages": [AIMessage(content="❌ Brak danych do analizy. Przekazuję do SQL agenta.")],
                "next_agent": "sql_agent"
            }
        
        # Sprawdź czy są rzeczywiste dane
        sql_data = sql_results[0] if sql_results else {}
        if sql_data.get("status") == "error":
            return {
                "messages": [AIMessage(content=f"❌ Nie mogę analizować - błąd SQL: {sql_data.get('error')}")],
                "next_agent": "supervisor"
            }
        
        # Wyodrębnij dane
        extracted_data = self._extract_data_from_sql_results(sql_results)
        
        # Jeśli nie ma danych do analizy
        if not extracted_data["has_data"]:
            return {
                "messages": [AIMessage(content="⚠️ Nie znalazłem danych do analizy w wynikach SQL.")],
                "analysis_results": {
                    "status": "no_data",
                    "message": "Brak danych do analizy"
                },
                "next_agent": "report_writer"
            }
        
        # Wykonaj szczegółową analizę
        analysis = ""
        
        # Analiza użytkowników social media
        if extracted_data["users"]:
            social_media_analysis = self._analyze_social_media_usage(extracted_data["users"])
            
            if social_media_analysis.get("top_user"):
                top_user = social_media_analysis["top_user"]
                analysis = f"""📊 **Analiza wykorzystania social media:**

🏆 **Użytkownik z największym czasem na social media:**
- **{top_user['name']}**
- Całkowity czas: **{top_user['total_hours']} godzin** ({top_user['total_seconds']} sekund)
- Liczba sesji: {top_user['sessions']}

📈 **TOP 5 użytkowników:**
"""
                for i, user in enumerate(social_media_analysis["top_5_users"], 1):
                    analysis += f"{i}. {user['name']}: {user['hours']} godzin\n"
                
                # Dodaj wnioski
                analysis += f"""
💡 **Wnioski:**
- Użytkownik {top_user['name']} spędza średnio {top_user['total_hours'] / max(top_user['sessions'], 1):.2f} godzin na sesję
- Jest to znacząco więcej niż pozostali użytkownicy
- Może to wskazywać na intensywne wykorzystanie mediów społecznościowych"""
        
        # Jeśli nie mamy analizy, użyj LLM
        if not analysis:
            response = self.chain.invoke({
                "messages": state["messages"],
                "sql_results": json.dumps(sql_results, indent=2, ensure_ascii=False)
            })
            analysis = response.content
        
        # Utwórz strukturyzowane wyniki analizy
        analysis_results = {
            "analysis": analysis,
            "timestamp": datetime.now().isoformat(),
            "data_summary": {
                "users_analyzed": len(extracted_data["users"]),
                "apps_analyzed": len(extracted_data["apps"]),
                "total_records": extracted_data["total_records"]
            },
            "extracted_data": extracted_data,
            "status": "success"
        }
        
        return {
            "messages": [AIMessage(content=analysis)],
            "analysis_results": analysis_results,
            "next_agent": "report_writer",
            "current_agent": "analyst"
        }