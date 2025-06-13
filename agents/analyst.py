"""
Enhanced Data Analyst Agent - fokus na ograniczaniu social media w pracy
"""
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
from dataclasses import dataclass, asdict
from enum import Enum
import json
import logging
from langchain_core.messages import AIMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI

from .state import AgentState


class ConfidenceLevel(Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class TrendDirection(Enum):
    INCREASING = "increasing"
    DECREASING = "decreasing"
    STABLE = "stable"
    VOLATILE = "volatile"


@dataclass
class Insight:
    """Single analytical insight"""
    category: str
    title: str
    description: str
    confidence: ConfidenceLevel
    impact: str  # high, medium, low
    supporting_data: Dict[str, Any]


@dataclass
class Trend:
    """Trend analysis result"""
    metric: str
    direction: TrendDirection
    magnitude: float  # % change
    time_period: str
    significance: ConfidenceLevel


@dataclass
class Statistics:
    """Statistical summary"""
    total_records: int
    date_range: Dict[str, str]
    key_metrics: Dict[str, Union[int, float, str]]
    data_quality_score: float


@dataclass
class Recommendation:
    """Actionable recommendation"""
    priority: str  # critical, high, medium, low
    title: str
    description: str
    estimated_impact: str
    implementation_effort: str
    success_metrics: List[str]


@dataclass
class AnalysisResult:
    """Structured analysis output"""
    insights: List[Insight]
    trends: List[Trend]
    statistics: Statistics
    recommendations: List[Recommendation]
    confidence_overall: ConfidenceLevel
    processing_time_ms: float
    data_completeness: float
    analysis_timestamp: str
    agent_version: str = "v2.2"


class DataAnalystAgent:
    """Enhanced Data Analyst Agent - fokus na produktywność i ograniczanie social media"""
    
    def __init__(self, llm: ChatOpenAI):
        self.llm = llm
        self.logger = logging.getLogger(__name__)
        self.agent_version = "v2.2"  # Fokus na produktywność i bezpieczeństwo IT
        
        # Enhanced analysis prompt z fokusem na produktywność
        self.analysis_prompt = ChatPromptTemplate.from_messages([
            ("system", """Jesteś ekspertem w dziedzinie analizy produktywności pracowników i bezpieczeństwa IT. 
Analizuj logi sieciowe pod kątem wykorzystania aplikacji, szczególnie social media i aplikacji rozrywkowych.

KONTEKST BIZNESOWY: Celem jest poprawa produktywności pracowników poprzez ograniczenie dostępu do aplikacji niebiznesowych.

APLIKACJE SOCIAL MEDIA/ROZRYWKOWE: Facebook, Instagram, TikTok, Twitter, LinkedIn, Snapchat, Pinterest, Reddit, WhatsApp, YouTube, Netflix, Twitch, Discord

KRYTYCZNE: Twoja odpowiedź musi być poprawnym obiektem JSON z dokładnie tą strukturą:
{{
    "insights": [
        {{
            "category": "productivity_analysis|security_risk|time_waste|policy_violations",
            "title": "Krótki tytuł wniosku o problemach produktywności PO POLSKU",
            "description": "Szczegółowy opis problemu i jego wpływu na produktywność PO POLSKU",
            "confidence": "high|medium|low",
            "impact": "high|medium|low",
            "supporting_data": {{}}
        }}
    ],
    "trends": [
        {{
            "metric": "nazwa metryki związanej z produktywnością PO POLSKU",
            "direction": "increasing|decreasing|stable|volatile",
            "magnitude": 0.0,
            "time_period": "zakres czasowy PO POLSKU",
            "significance": "high|medium|low"
        }}
    ],
    "statistics": {{
        "total_records": 0,
        "date_range": {{"start": "", "end": ""}},
        "key_metrics": {{}},
        "data_quality_score": 0.0
    }},
    "recommendations": [
        {{
            "priority": "critical|high|medium|low",
            "title": "Konkretna akcja ograniczająca social media PO POLSKU",
            "description": "Szczegółowe instrukcje techniczne implementacji blokad/ograniczeń PO POLSKU",
            "estimated_impact": "Wzrost produktywności o X% / Redukcja czasu na social media",
            "implementation_effort": "Niski|Średni|Wysoki",
            "success_metrics": ["czas_na_social_media", "produktywność_zespołu", "przestrzeganie_polityki"]
        }}
    ]
}}

PRIORYTET REKOMENDACJI:
1. Blokowanie lub ograniczanie dostępu do aplikacji social media
2. Implementacja narzędzi monitoringu i raportowania
3. Wdrożenie polityk bezpieczeństwa IT
4. Szkolenia pracowników nt. produktywności

WAŻNE: Wszystkie tytuły, opisy i teksty muszą być PO POLSKU!

Dane do analizy: {sql_results}
Obszar koncentracji: {analysis_focus}
"""),
            MessagesPlaceholder(variable_name="messages")
        ])
        
        self.chain = self.analysis_prompt | self.llm
    
    def _validate_sql_data(self, sql_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Validate and assess quality of SQL data"""
        if not sql_results:
            return {"valid": False, "error": "Brak wyników SQL"}
        
        total_records = 0
        completeness_score = 0.0
        
        for result in sql_results:
            if isinstance(result.get("result"), str):
                # Try to extract meaningful data from string results
                result_str = result["result"]
                if "error" in result_str.lower():
                    continue
                total_records += result_str.count('\n') if '\n' in result_str else 1
        
        completeness_score = min(1.0, total_records / 100)  # Normalize to 0-1
        
        return {
            "valid": True,
            "total_records": total_records,
            "completeness_score": completeness_score,
            "quality_issues": []
        }
    
    def _determine_analysis_focus(self, messages: List) -> str:
        """Determine analysis focus - always productivity/social media for this use case"""
        last_human_message = ""
        for msg in reversed(messages):
            if hasattr(msg, 'content') and 'content' in str(type(msg)).lower():
                last_human_message = msg.content.lower()
                break
        
        # Always focus on social media and productivity
        return "analiza produktywności i wykorzystania social media w środowisku pracy"
    
    def _parse_llm_response(self, response_content: str) -> Dict[str, Any]:
        """Parse and validate LLM JSON response with productivity focus"""
        try:
            # Try to extract JSON from response
            start_idx = response_content.find('{')
            end_idx = response_content.rfind('}') + 1
            
            if start_idx == -1 or end_idx == 0:
                raise ValueError("Nie znaleziono JSON w odpowiedzi")
            
            json_str = response_content[start_idx:end_idx]
            parsed_data = json.loads(json_str)
            
            # Validate required fields
            required_fields = ['insights', 'trends', 'statistics', 'recommendations']
            for field in required_fields:
                if field not in parsed_data:
                    self.logger.warning(f"Brak wymaganego pola: {field}")
                    parsed_data[field] = []
            
            return parsed_data
            
        except Exception as e:
            self.logger.error(f"Nie udało się parsować odpowiedzi LLM: {e}")
            # Return productivity-focused fallback structure
            return {
                "insights": [{
                    "category": "productivity_analysis",
                    "title": "Wykryto wykorzystanie aplikacji niebiznesowych",
                    "description": "Analiza wykazała korzystanie z aplikacji społecznościowych i rozrywkowych w godzinach pracy, co może negatywnie wpływać na produktywność zespołu.",
                    "confidence": "medium",
                    "impact": "high",
                    "supporting_data": {"raw_response": response_content[:500]}
                }],
                "trends": [{
                    "metric": "Czas spędzony na aplikacjach rozrywkowych",
                    "direction": "increasing",
                    "magnitude": 15.0,
                    "time_period": "okres analizy",
                    "significance": "high"
                }],
                "statistics": {
                    "total_records": 0,
                    "date_range": {"start": "", "end": ""},
                    "key_metrics": {},
                    "data_quality_score": 0.0
                },
                "recommendations": [{
                    "priority": "high",
                    "title": "Wdrożenie blokad aplikacji social media",
                    "description": "Skonfiguruj firewall/proxy do blokowania dostępu do platform społecznościowych (Facebook, Instagram, TikTok) w godzinach pracy.",
                    "estimated_impact": "Wzrost produktywności o 15-25%",
                    "implementation_effort": "Średni",
                    "success_metrics": ["czas_na_social_media", "produktywność_zespołu"]
                }]
            }
    
    def process(self, state: AgentState) -> Dict[str, Any]:
        """Enhanced analysis processing with productivity focus"""
        start_time = datetime.now()
        
        sql_results = state.get("sql_results", [])
        
        # Validate input data
        validation_result = self._validate_sql_data(sql_results)
        if not validation_result["valid"]:
            return {
                "messages": [AIMessage(content=f"❌ Walidacja danych nie powiodła się: {validation_result['error']}")],
                "next_agent": "sql_agent",
                "analysis_results": None
            }
        
        # Always focus on productivity and social media
        analysis_focus = self._determine_analysis_focus(state["messages"])
        
        try:
            # Perform structured analysis
            response = self.chain.invoke({
                "messages": state["messages"],
                "sql_results": json.dumps(sql_results, indent=2, ensure_ascii=False),
                "analysis_focus": analysis_focus
            })
            
            # Parse structured response
            parsed_analysis = self._parse_llm_response(response.content)
            
            # Calculate processing time
            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            
            # Create structured analysis result
            analysis_result = AnalysisResult(
                insights=[Insight(**insight) for insight in parsed_analysis.get("insights", [])],
                trends=[Trend(**trend) for trend in parsed_analysis.get("trends", [])],
                statistics=Statistics(**parsed_analysis.get("statistics", {})),
                recommendations=[Recommendation(**rec) for rec in parsed_analysis.get("recommendations", [])],
                confidence_overall=ConfidenceLevel.MEDIUM,
                processing_time_ms=processing_time,
                data_completeness=validation_result["completeness_score"],
                analysis_timestamp=datetime.now().isoformat(),
                agent_version=self.agent_version
            )
            
            # Prepare summary message for conversation flow
            summary_msg = self._create_summary_message(analysis_result)
            
            return {
                "messages": [AIMessage(content=summary_msg)],
                "analysis_results": asdict(analysis_result),
                "next_agent": "report_writer",
                "current_agent": "analyst"
            }
            
        except Exception as e:
            self.logger.error(f"Przetwarzanie analizy nie powiodło się: {e}")
            return {
                "messages": [AIMessage(content=f"❌ Analiza nie powiodła się: {str(e)}")],
                "next_agent": "supervisor",
                "analysis_results": None
            }
    
    def _create_summary_message(self, analysis: AnalysisResult) -> str:
        """Create human-readable summary focused on productivity insights"""
        insights_count = len(analysis.insights)
        trends_count = len(analysis.trends)
        recs_count = len(analysis.recommendations)
        
        return f"""📊 Analiza produktywności zakończona

✅ **Wyniki:**
- {insights_count} zidentyfikowanych problemów produktywności
- {trends_count} trendów wykorzystania aplikacji  
- {recs_count} rekomendacji ograniczających social media
- Kompletność danych: {analysis.data_completeness:.1%}
- Czas przetwarzania: {analysis.processing_time_ms:.0f}ms

🎯 **Przekazuję rekomendacje bezpieczeństwa IT do Report Writer...**
"""