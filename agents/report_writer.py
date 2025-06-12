"""
Enhanced Report Writer Agent - consumes structured analysis data
"""
import logging
from typing import Dict, Any, List
from datetime import datetime
from langchain_core.messages import AIMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI

from .state import AgentState


class ReportWriterAgent:
    """Enhanced Report Writer consuming structured analysis data"""
    
    def __init__(self, llm: ChatOpenAI):
        self.llm = llm
        self.agent_version = "v2.0"
        self.logger = logging.getLogger(__name__)
        
        self.report_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a professional Report Writer. Create comprehensive, executive-ready reports.

Use the structured analysis data to create a polished report with:
1. Executive Summary (2-3 sentences)
2. Key Findings (bullet points)
3. Trends & Patterns
4. Actionable Recommendations
5. Supporting Data

Use markdown formatting for clarity.

Structured Analysis Data:
{analysis_data}

Raw SQL Results (for context):
{sql_results}
"""),
            MessagesPlaceholder(variable_name="messages")
        ])
        
        self.chain = self.report_prompt | self.llm
    
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
        """Generate executive summary from structured data"""
        insights = analysis.get('insights', [])
        high_impact_insights = [i for i in insights if i.get('impact') == 'high']
        
        total_records = analysis.get('statistics', {}).get('total_records', 0)
        confidence = analysis.get('confidence_overall', 'medium')
        
        return f"""
## 🎯 Executive Summary

Analysis of {total_records:,} data records reveals {len(high_impact_insights)} high-impact insights with {confidence} confidence level. 
{self._get_top_insight_summary(high_impact_insights)}
"""
    
    def _get_top_insight_summary(self, insights: List[Dict]) -> str:
        """Get summary of most important insight"""
        if not insights:
            return "Detailed patterns and trends identified in the data require further investigation."
        
        top_insight = insights[0]  # Assuming first is most important
        return f"Key finding: {top_insight.get('title', 'Critical insight identified')}."
    
    def _format_insights_section(self, insights: List[Dict]) -> str:
        """Format insights into readable sections"""
        if not insights:
            return "## 📊 Key Findings\n\nNo significant insights identified."
        
        sections = {
            'usage_patterns': '### 📈 Usage Patterns',
            'performance': '### ⚡ Performance Analysis', 
            'security': '### 🔒 Security Insights',
            'trends': '### 📊 Trend Analysis'
        }
        
        output = "## 📊 Key Findings\n\n"
        
        for category, title in sections.items():
            category_insights = [i for i in insights if i.get('category') == category]
            if category_insights:
                output += f"{title}\n\n"
                for insight in category_insights:
                    confidence_emoji = {"high": "🟢", "medium": "🟡", "low": "🔴"}.get(insight.get('confidence', 'medium'), "🟡")
                    impact_emoji = {"high": "🚨", "medium": "⚠️", "low": "ℹ️"}.get(insight.get('impact', 'medium'), "⚠️")
                    
                    output += f"- **{insight.get('title', 'Insight')}** {confidence_emoji} {impact_emoji}\n"
                    output += f"  {insight.get('description', 'No description available')}\n\n"
        
        return output
    
    def _is_fully_structured(self, analysis_results: Dict[str, Any]) -> bool:
        """Check if analysis results are fully structured"""
        required_keys = ['insights', 'trends', 'statistics', 'recommendations']
        return all(key in analysis_results for key in required_keys)
    
    def _create_simple_summary(self, analysis_results: Dict[str, Any]) -> str:
        """Create simple summary for partial data"""
        return f"""
## 🎯 Executive Summary

Analysis completed with available data. Key findings and recommendations are presented below based on the current dataset.
"""
    
    def _format_available_data(self, analysis_results: Dict[str, Any]) -> str:
        """Format whatever data is available"""
        output = "## 📊 Available Analysis\n\n"
        
        # Handle legacy format or partial data
        if 'analysis' in analysis_results:
            output += f"{analysis_results['analysis']}\n\n"
        
        if 'insights' in analysis_results and analysis_results['insights']:
            insights = analysis_results['insights']
            if isinstance(insights, list):
                output += "### Key Insights\n\n"
                for i, insight in enumerate(insights, 1):
                    if isinstance(insight, dict):
                        title = insight.get('title', f'Insight {i}')
                        desc = insight.get('description', 'No description available')
                        output += f"- **{title}**: {desc}\n"
                    else:
                        output += f"- {insight}\n"
                output += "\n"
        
        return output
    
    def _format_sql_data_summary(self, sql_results: List[Dict]) -> str:
        """Create summary from SQL results when analysis is limited"""
        if not sql_results:
            return ""
        
        output = "## 📋 Data Summary\n\n"
        
        for result in sql_results:
            if 'result' in result and result['result']:
                result_str = str(result['result'])
                if 'Application' in result_str and 'Duration' in result_str:
                    output += "### Application Usage Data\n\n"
                    output += "Raw data extracted from network logs:\n\n"
                    output += f"```\n{result_str}\n```\n\n"
                    break
        
        return output
    
    def _create_fallback_report(self, sql_results: List[Dict]) -> str:
        """Create basic report from SQL data only"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        return f"""
# 📊 Data Analysis Report

## 🎯 Executive Summary

Basic data extraction completed. Analysis pipeline encountered issues, but raw data is available for review.

{self._format_sql_data_summary(sql_results)}

## 🔧 Recommendations

1. **Review Analysis Pipeline**: Check data analyst configuration and processing
2. **Validate Data Quality**: Ensure data formats are consistent 
3. **Monitor System Health**: Implement better error handling and monitoring

---
**Report Generated**: {timestamp} | **Agent Version**: {self.agent_version}  
**Status**: Fallback Mode - Limited Analysis Available
"""
    
    def _create_error_report(self, error: Exception, analysis_results: Dict, sql_results: List) -> str:
        """Create comprehensive error report"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        return f"""
# 📊 Data Analysis Report

## ❌ Report Generation Error

**Error Details:**
- Exception: {type(error).__name__}
- Message: {str(error)}
- Timestamp: {timestamp}

**System Status:**
- Analysis Results: {'✅ Available' if analysis_results else '❌ Missing'}
- SQL Results: {len(sql_results)} queries executed
- Data Available: {'✅' if sql_results else '❌'}

**Available Data Preview:**
{self._format_sql_data_summary(sql_results) if sql_results else 'No SQL data available'}

**Immediate Actions Required:**
1. **Check Agent Logs**: Review detailed error logs for root cause
2. **Validate Data Contracts**: Ensure data formats match expected schemas
3. **Test Agent Communication**: Verify agent-to-agent data passing
4. **Fallback Procedures**: Implement manual report generation if needed

**Contact Information:**
- System Administrator: Check monitoring dashboards
- Technical Support: Review agent health metrics
- Data Team: Validate data quality and formats

---
**Report Generated**: {timestamp} | **Agent Version**: {self.agent_version}  
**Status**: Error Recovery Mode
"""
    
    def _format_trends_section(self, trends: List[Dict]) -> str:
        """Format trends analysis"""
        if not trends:
            return "## 📈 Trends & Patterns\n\nNo clear trends identified in the analyzed period.\n\n"
        
        output = "## 📈 Trends & Patterns\n\n"
        
        for trend in trends:
            direction_emoji = {
                "increasing": "📈",
                "decreasing": "📉", 
                "stable": "➡️",
                "volatile": "📊"
            }.get(trend.get('direction', 'stable'), "➡️")
            
            magnitude = trend.get('magnitude', 0)
            magnitude_str = f"{magnitude:+.1f}%" if magnitude != 0 else "stable"
            
            output += f"- **{trend.get('metric', 'Unknown metric')}** {direction_emoji}\n"
            output += f"  Change: {magnitude_str} over {trend.get('time_period', 'analyzed period')}\n"
            output += f"  Significance: {trend.get('significance', 'medium')}\n\n"
        
        return output
    
    def _format_recommendations_section(self, recommendations: List[Dict]) -> str:
        """Format actionable recommendations"""
        if not recommendations:
            return "## 🎯 Recommendations\n\nNo specific recommendations at this time.\n\n"
        
        output = "## 🎯 Actionable Recommendations\n\n"
        
        # Group by priority
        priority_order = ['critical', 'high', 'medium', 'low']
        
        for priority in priority_order:
            priority_recs = [r for r in recommendations if r.get('priority') == priority]
            if not priority_recs:
                continue
                
            priority_emoji = {"critical": "🚨", "high": "🔥", "medium": "⚠️", "low": "💡"}.get(priority, "💡")
            output += f"### {priority_emoji} {priority.title()} Priority\n\n"
            
            for i, rec in enumerate(priority_recs, 1):
                output += f"**{i}. {rec.get('title', 'Recommendation')}**\n\n"
                output += f"{rec.get('description', 'No description available')}\n\n"
                output += f"- **Impact**: {rec.get('estimated_impact', 'Unknown')}\n"
                output += f"- **Effort**: {rec.get('implementation_effort', 'Unknown')}\n"
                
                success_metrics = rec.get('success_metrics', [])
                if success_metrics:
                    output += f"- **Success Metrics**: {', '.join(success_metrics)}\n"
                output += "\n"
        
        return output
    
    def _format_supporting_data(self, analysis: Dict[str, Any]) -> str:
        """Format supporting statistics and metadata"""
        stats = analysis.get('statistics', {})
        
        output = "## 📋 Supporting Data\n\n"
        output += "### Dataset Overview\n\n"
        output += f"- **Total Records**: {stats.get('total_records', 0):,}\n"
        
        date_range = stats.get('date_range', {})
        if date_range.get('start') and date_range.get('end'):
            output += f"- **Date Range**: {date_range['start']} to {date_range['end']}\n"
        
        output += f"- **Data Quality Score**: {stats.get('data_quality_score', 0):.1%}\n"
        output += f"- **Analysis Completeness**: {analysis.get('data_completeness', 0):.1%}\n"
        output += f"- **Processing Time**: {analysis.get('processing_time_ms', 0):.0f}ms\n\n"
        
        key_metrics = stats.get('key_metrics', {})
        if key_metrics:
            output += "### Key Metrics\n\n"
            for metric, value in key_metrics.items():
                output += f"- **{metric}**: {value}\n"
            output += "\n"
        
        return output
    
    def process(self, state: AgentState) -> Dict[str, Any]:
        """Create comprehensive report from structured analysis data"""
        analysis_results = state.get("analysis_results")
        sql_results = state.get("sql_results", [])
        
        # Validate analysis data
        if not self._validate_analysis_data(analysis_results):
            fallback_msg = """
# 📊 Data Analysis Report

## ⚠️ Limited Analysis Available

The analysis data was not available in the expected structured format. 
This may indicate an issue with the data analysis pipeline.

**Recommendation**: Review the data analysis process and ensure proper data validation.
"""
            return {
                "messages": [AIMessage(content=fallback_msg)],
                "next_agent": "end",
                "current_agent": "report_writer"
            }
        
        try:
            # Build comprehensive report using structured data
            report_sections = [
                self._create_executive_summary(analysis_results),
                self._format_insights_section(analysis_results.get('insights', [])),
                self._format_trends_section(analysis_results.get('trends', [])),
                self._format_recommendations_section(analysis_results.get('recommendations', [])),
                self._format_supporting_data(analysis_results)
            ]
            
            # Combine all sections
            full_report = "\n".join(report_sections)
            
            # Add report metadata
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            # Safe confidence formatting
            confidence_val = analysis_results.get('confidence_overall', 'medium')
            if hasattr(confidence_val, 'value'):
                confidence_str = confidence_val.value.title()
            else:
                confidence_str = str(confidence_val).title()
            
            final_report = f"""
# 📊 Data Analysis Report

{full_report}

---
**Report Generated**: {timestamp} | **Agent Version**: {self.agent_version}  
**Analysis Confidence**: {confidence_str}
"""
            
            return {
                "messages": [AIMessage(content=final_report)],
                "next_agent": "end",
                "current_agent": "report_writer"
            }
            
        except Exception as e:
            error_report = f"""
# 📊 Data Analysis Report

## ❌ Report Generation Error

An error occurred while generating the comprehensive report: {str(e)}

**Available Data Summary:**
- Analysis Results: {'✅ Available' if analysis_results else '❌ Missing'}
- SQL Results: {len(sql_results)} queries executed
- Timestamp: {datetime.now().isoformat()}

**Next Steps:**
1. Review the data analysis pipeline
2. Check for data formatting issues
3. Validate agent communication protocols
"""
            
            return {
                "messages": [AIMessage(content=error_report)],
                "next_agent": "end",
                "current_agent": "report_writer"
            }