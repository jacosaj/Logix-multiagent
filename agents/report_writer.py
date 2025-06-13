"""
Enhanced Report Writer Agent - poprawione formatowanie jednostek czasu
"""
import logging
from typing import Dict, Any, List
from datetime import datetime, timedelta
from langchain_core.messages import AIMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI

from .state import AgentState


class ReportWriterAgent:
    """Enhanced Report Writer - polskie raporty z poprawnym formatowaniem czasu"""
    
    def __init__(self, llm: ChatOpenAI):
        self.llm = llm
        self.agent_version = "v2.2"  # Zwiększona wersja
        self.logger = logging.getLogger(__name__)
        
        self.report_prompt = ChatPromptTemplate.from_messages([
            ("system", """Jesteś profesjonalnym Autorem Raportów. Tworzysz kompleksowe raporty po angielsku.

Wykorzystaj dane z analizy strukturyzowanej do stworzenia raportu zawierającego:
1. Streszczenie zarządcze (2-3 zdania)
2. Kluczowe wnioski (punkty)
3. Trendy i wzorce
4. Rekomendacje do działania 
5. Dane wspierające

Używaj formatowania markdown dla czytelności. Wszystkie teksty MUSZĄ być po angielsku.

Dane z analizy strukturyzowanej:
{analysis_data}

Surowe wyniki SQL (dla kontekstu):
{sql_results}
"""),
            MessagesPlaceholder(variable_name="messages")
        ])
        
        self.chain = self.report_prompt | self.llm
    
    def _format_duration(self, milliseconds: float) -> str:
        """
        Formatuj czas z MILISEKUND na czytelny format
        """
        if not milliseconds or milliseconds <= 0:
            return "0 sekund"
        
        # KLUCZOWA POPRAWKA: Konwertuj z milisekund na sekundy
        seconds = milliseconds / 1000.0
        
        # Konwertuj na różne jednostki
        hours = seconds / 3600
        minutes = seconds / 60
        days = hours / 24
        
        if days >= 1:
            return f"{days:.1f} dni ({hours:.1f} godzin)"
        elif hours >= 1:
            return f"{hours:.1f} godzin ({minutes:.0f} minut)"
        elif minutes >= 1:
            return f"{minutes:.1f} minut"
        else:
            return f"{seconds:.0f} sekund"
    
    def _format_bytes(self, bytes_value: float) -> str:
        """Formatuj bajty na czytelny format"""
        if not bytes_value or bytes_value <= 0:
            return "0 B"
        
        units = ['B', 'KB', 'MB', 'GB', 'TB']
        unit_index = 0
        size = float(bytes_value)
        
        while size >= 1024.0 and unit_index < len(units) - 1:
            size /= 1024.0
            unit_index += 1
        
        return f"{size:.1f} {units[unit_index]}"
    
    def _format_number(self, number: float) -> str:
        """Formatuj liczby z separatorami tysięcy"""
        if isinstance(number, (int, float)):
            return f"{number:,.0f}".replace(",", " ")
        return str(number)
    
    def _detect_duration_field(self, metric_name: str) -> bool:
        """
        Wykryj czy pole zawiera dane czasowe w milisekundach
        Ulepszona logika rozpoznawania pól czasowych
        """
        duration_indicators = [
            'duration', 'time', 'czas', 'total_duration', 
            'average_duration', 'session_time', 'uptime'
        ]
        return any(indicator in metric_name.lower() for indicator in duration_indicators)
    
    def _validate_analysis_data(self, analysis_results: Dict[str, Any]) -> bool:
        """Validate that we have properly structured analysis data"""
        if not analysis_results:
            return False
        
        # Check if it's the legacy format (just a string)
        if isinstance(analysis_results, str):
            return False
        
        # Check for structured format
        required_keys = ['insights', 'trends', 'statistics', 'recommendations']
        has_structured_keys = all(key in analysis_results for key in required_keys)
        
        # Also accept if we have at least some analysis content
        has_some_content = any(key in analysis_results for key in ['insights', 'analysis', 'content'])
        
        return has_structured_keys or has_some_content
    
    def _create_executive_summary(self, analysis: Dict[str, Any]) -> str:
        """Generuj polskie streszczenie zarządcze"""
        insights = analysis.get('insights', [])
        high_impact_insights = [i for i in insights if i.get('impact') == 'high']
        
        total_records = analysis.get('statistics', {}).get('total_records', 0)
        confidence = analysis.get('confidence_overall', 'medium')
        
        # Mapowanie poziomów pewności na polski
        confidence_map = {
            'high': 'wysokim',
            'medium': 'średnim', 
            'low': 'niskim'
        }
        confidence_pl = confidence_map.get(confidence, 'średnim')
        
        formatted_records = self._format_number(total_records)
        
        return f"""
## 🎯 Streszczenie Zarządcze

Analiza {formatted_records} rekordów danych ujawnia {len(high_impact_insights)} kluczowych wniosków o {confidence_pl} poziomie pewności. 
{self._get_top_insight_summary(high_impact_insights)}
"""
    
    def _get_top_insight_summary(self, insights: List[Dict]) -> str:
        """Podsumowanie najważniejszego wniosku po polsku"""
        if not insights:
            return "Zidentyfikowano szczegółowe wzorce i trendy w danych wymagające dalszej analizy."
        
        top_insight = insights[0]
        return f"Główny wniosek: {top_insight.get('title', 'Zidentyfikowano krytyczny wzorzec')}."
    
    def _format_insights_section(self, insights: List[Dict]) -> str:
        """Formatuj sekcję wniosków po polsku"""
        if not insights:
            return "## 📊 Kluczowe Wnioski\n\nNie zidentyfikowano znaczących wniosków.\n\n"
        
        sections = {
            'usage_patterns': '### 📈 Wzorce Użytkowania',
            'performance': '### ⚡ Analiza Wydajności', 
            'security': '### 🔒 Wnioski Bezpieczeństwa',
            'trends': '### 📊 Analiza Trendów'
        }
        
        output = "## 📊 Kluczowe Wnioski\n\n"
        
        for category, title in sections.items():
            category_insights = [i for i in insights if i.get('category') == category]
            if category_insights:
                output += f"{title}\n\n"
                for insight in category_insights:
                    confidence_emoji = {"high": "🟢", "medium": "🟡", "low": "🔴"}.get(insight.get('confidence', 'medium'), "🟡")
                    impact_emoji = {"high": "🚨", "medium": "⚠️", "low": "ℹ️"}.get(insight.get('impact', 'medium'), "⚠️")
                    
                    output += f"- **{insight.get('title', 'Wniosek')}** {confidence_emoji} {impact_emoji}\n"
                    output += f"  {insight.get('description', 'Brak opisu')}\n\n"
        
        return output
    
    def _format_trends_section(self, trends: List[Dict]) -> str:
        """Formatuj sekcję trendów po polsku"""
        if not trends:
            return "## 📈 Trendy i Wzorce\n\nNie zidentyfikowano wyraźnych trendów w analizowanym okresie.\n\n"
        
        output = "## 📈 Trendy i Wzorce\n\n"
        
        direction_map = {
            "increasing": ("📈", "wzrost"),
            "decreasing": ("📉", "spadek"), 
            "stable": ("➡️", "stabilny"),
            "volatile": ("📊", "niestabilny")
        }
        
        for trend in trends:
            direction = trend.get('direction', 'stable')
            direction_emoji, direction_pl = direction_map.get(direction, ("➡️", "stabilny"))
            
            magnitude = trend.get('magnitude', 0)
            if magnitude != 0:
                magnitude_str = f"{magnitude:+.1f}%"
            else:
                magnitude_str = "bez zmian"
            
            output += f"- **{trend.get('metric', 'Nieznana metryka')}** {direction_emoji}\n"
            output += f"  Zmiana: {magnitude_str} ({direction_pl}) w okresie {trend.get('time_period', 'analizowanym')}\n"
            output += f"  Istotność: {trend.get('significance', 'średnia')}\n\n"
        
        return output
    
    def _format_recommendations_section(self, recommendations: List[Dict]) -> str:
        """Formatuj rekomendacje po polsku"""
        if not recommendations:
            return "## 🎯 Rekomendacje\n\nBrak konkretnych rekomendacji w tym momencie.\n\n"
        
        output = "## 🎯 Rekomendacje do Działania\n\n"
        
        # Mapowanie priorytetów
        priority_map = {
            'critical': ('🚨', 'Krytyczny'),
            'high': ('🔥', 'Wysoki'),
            'medium': ('⚠️', 'Średni'),
            'low': ('💡', 'Niski')
        }
        
        priority_order = ['critical', 'high', 'medium', 'low']
        
        for priority in priority_order:
            priority_recs = [r for r in recommendations if r.get('priority') == priority]
            if not priority_recs:
                continue
                
            priority_emoji, priority_pl = priority_map.get(priority, ("💡", "Niski"))
            output += f"### {priority_emoji} Priorytet {priority_pl}\n\n"
            
            for i, rec in enumerate(priority_recs, 1):
                output += f"**{i}. {rec.get('title', 'Rekomendacja')}**\n\n"
                output += f"{rec.get('description', 'Brak opisu')}\n\n"
                output += f"- **Wpływ**: {rec.get('estimated_impact', 'Nieznany')}\n"
                output += f"- **Nakład pracy**: {rec.get('implementation_effort', 'Nieznany')}\n"
                
                success_metrics = rec.get('success_metrics', [])
                if success_metrics:
                    output += f"- **Metryki sukcesu**: {', '.join(success_metrics)}\n"
                output += "\n"
        
        return output
    
    def _format_supporting_data(self, analysis: Dict[str, Any]) -> str:
        """
        Formatuj dane wspierające po polsku 
        POPRAWKA: Poprawione formatowanie czasu z milisekund
        """
        stats = analysis.get('statistics', {})
        
        output = "## 📋 Dane Wspierające\n\n"
        output += "### Przegląd Zestawu Danych\n\n"
        
        total_records = stats.get('total_records', 0)
        output += f"- **Łączna liczba rekordów**: {self._format_number(total_records)}\n"
        
        date_range = stats.get('date_range', {})
        if date_range.get('start') and date_range.get('end'):
            output += f"- **Zakres dat**: {date_range['start']} do {date_range['end']}\n"
        
        quality_score = stats.get('data_quality_score', 0)
        output += f"- **Ocena jakości danych**: {quality_score:.1%}\n"
        
        completeness = analysis.get('data_completeness', 0)
        output += f"- **Kompletność analizy**: {completeness:.1%}\n"
        
        processing_time = analysis.get('processing_time_ms', 0)
        output += f"- **Czas przetwarzania**: {processing_time:.0f} ms\n\n"
        
        key_metrics = stats.get('key_metrics', {})
        if key_metrics:
            output += "### Kluczowe Metryki\n\n"
            for metric, value in key_metrics.items():
                # POPRAWKA: Ulepszona logika formatowania wartości czasowych
                if self._detect_duration_field(metric):
                    if isinstance(value, (int, float)):
                        formatted_value = self._format_duration(value)  # Teraz poprawnie z ms
                    else:
                        formatted_value = str(value)
                elif 'byte' in metric.lower():
                    if isinstance(value, (int, float)):
                        formatted_value = self._format_bytes(value)
                    else:
                        formatted_value = str(value)
                else:
                    if isinstance(value, (int, float)):
                        formatted_value = self._format_number(value)
                    else:
                        formatted_value = str(value)
                
                output += f"- **{metric}**: {formatted_value}\n"
            output += "\n"
        
        return output
    
    def process(self, state: AgentState) -> Dict[str, Any]:
        """Stwórz kompleksowy raport z danych analizy strukturyzowanej"""
        analysis_results = state.get("analysis_results")
        sql_results = state.get("sql_results", [])
        
        # Validuj dane analizy
        if not self._validate_analysis_data(analysis_results):
            fallback_msg = """
# 📊 Raport Analizy Danych

## ⚠️ Ograniczona Analiza Dostępna

Dane analizy nie były dostępne w oczekiwanym formacie strukturizowanym. 
Może to wskazywać na problem z procesem analizy danych.

**Rekomendacja**: Przejrzyj proces analizy danych i upewnij się o prawidłowej walidacji danych.
"""
            return {
                "messages": [AIMessage(content=fallback_msg)],
                "next_agent": "end",
                "current_agent": "report_writer"
            }
        
        try:
            # Buduj kompleksowy raport używając danych strukturyzowanych
            report_sections = [
                self._create_executive_summary(analysis_results),
                self._format_insights_section(analysis_results.get('insights', [])),
                self._format_trends_section(analysis_results.get('trends', [])),
                self._format_recommendations_section(analysis_results.get('recommendations', [])),
                self._format_supporting_data(analysis_results)
            ]
            
            # Połącz wszystkie sekcje
            full_report = "\n".join(report_sections)
            
            # Dodaj metadane raportu
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # Bezpieczne formatowanie poziomu pewności
            confidence_val = analysis_results.get('confidence_overall', 'medium')
            if hasattr(confidence_val, 'value'):
                confidence_str = confidence_val.value
            else:
                confidence_str = str(confidence_val)
            
            # Mapuj na polski
            confidence_map = {
                'high': 'Wysoki',
                'medium': 'Średni', 
                'low': 'Niski'
            }
            confidence_pl = confidence_map.get(confidence_str.lower(), 'Średni')
            
            final_report = f"""
# 📊 Raport Analizy Danych

{full_report}

---
**Raport wygenerowany**: {timestamp} | **Wersja agenta**: {self.agent_version}  
**Poziom pewności analizy**: {confidence_pl}
"""
            
            return {
                "messages": [AIMessage(content=final_report)],
                "next_agent": "end",
                "current_agent": "report_writer"
            }
            
        except Exception as e:
            self.logger.error(f"Błąd generowania raportu: {e}")
            error_report = f"""
# 📊 Raport Analizy Danych

## ❌ Błąd Generowania Raportu

Wystąpił błąd podczas tworzenia kompleksowego raportu: {str(e)}

**Podsumowanie Dostępnych Danych:**
- Wyniki analizy: {'✅ Dostępne' if analysis_results else '❌ Brak'}
- Wyniki SQL: {len(sql_results)} wykonanych zapytań
- Znacznik czasu: {datetime.now().isoformat()}

**Kolejne Kroki:**
1. Przejrzyj proces analizy danych
2. Sprawdź problemy z formatowaniem danych
3. Zweryfikuj protokoły komunikacji między agentami
"""
            
            return {
                "messages": [AIMessage(content=error_report)],
                "next_agent": "end",
                "current_agent": "report_writer"
            }