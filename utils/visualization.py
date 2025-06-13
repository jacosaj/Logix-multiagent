"""
Wizualizacja grafu multi-agentowego - uproszczona wersja
"""
import streamlit as st
from typing import Dict, Any


class GraphVisualizer:
    """Klasa do wizualizacji grafu agentów - statyczna wersja"""
    
    @staticmethod
    def get_static_mermaid_code() -> str:
        """Zwróć statyczny kod Mermaid dla architektury systemu"""
        return """graph TD
    start([🚀 START])
    supervisor["👔 Supervisor"]
    sql_agent["🗄️ SQL Agent"]
    analyst["📊 Data Analyst"]
    report_writer["📝 Report Writer"]
    end_node([🏁 END])
    
    start --> supervisor
    supervisor --> sql_agent
    supervisor --> analyst
    supervisor --> report_writer
    supervisor --> end_node
    sql_agent --> supervisor
    sql_agent --> analyst
    sql_agent --> report_writer
    sql_agent --> end_node
    analyst --> supervisor
    analyst --> report_writer
    analyst --> end_node
    report_writer --> supervisor
    report_writer --> end_node
    
    %% Style węzłów
    style start fill:#ffa07a,stroke:#333,color:white,stroke-width:2px
    style supervisor fill:#ff6b6b,stroke:#333,color:white,stroke-width:2px
    style sql_agent fill:#4ecdc4,stroke:#333,color:white,stroke-width:2px
    style analyst fill:#45b7d1,stroke:#333,color:white,stroke-width:2px
    style report_writer fill:#96ceb4,stroke:#333,color:white,stroke-width:2px
    style end_node fill:#dda0dd,stroke:#333,color:white,stroke-width:2px"""
    
    @staticmethod
    def show_static_graph(title="🔄 Architektura systemu multi-agentowego"):
        """Wyświetl statyczny graf architektury"""
        st.markdown(f"### {title}")
        
        mermaid_code = GraphVisualizer.get_static_mermaid_code()
        
        # HTML z Mermaid
        mermaid_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <script src="https://cdn.jsdelivr.net/npm/mermaid@10.6.1/dist/mermaid.min.js"></script>
            <style>
                body {{ 
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    margin: 0;
                    padding: 20px;
                    background-color: #ffffff;
                }}
                .mermaid {{
                    text-align: center;
                    background-color: #ffffff;
                }}
            </style>
        </head>
        <body>
            <div class="mermaid">
{mermaid_code}
            </div>
            
            <script>
                mermaid.initialize({{
                    startOnLoad: true,
                    theme: 'default',
                    flowchart: {{ 
                        useMaxWidth: true,
                        htmlLabels: true,
                        curve: 'basis'
                    }},
                    securityLevel: 'loose'
                }});
            </script>
        </body>
        </html>
        """
        
        st.components.v1.html(mermaid_html, height=600, scrolling=True)
    
    @staticmethod
    def get_architecture_stats() -> Dict[str, Any]:
        """Zwróć statystyki architektury"""
        return {
            "total_nodes": 6,
            "total_edges": 14,
            "agent_count": 4,
            "agents": ["Supervisor", "SQL Agent", "Data Analyst", "Report Writer"]
        }
    
    @staticmethod
    def export_to_html(filename="multi_agent_architecture.html") -> str:
        """Eksportuj statyczny graf do HTML"""
        mermaid_code = GraphVisualizer.get_static_mermaid_code()
        
        html_template = f"""<!DOCTYPE html>
<html lang="pl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Multi-Agent System - Architektura</title>
    <script src="https://cdn.jsdelivr.net/npm/mermaid@10.6.1/dist/mermaid.min.js"></script>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            padding: 30px;
        }}
        h1 {{
            text-align: center;
            color: #333;
            margin-bottom: 30px;
        }}
        .graph-container {{
            text-align: center;
            margin: 20px 0;
        }}
        .stats {{
            display: flex;
            justify-content: space-around;
            margin: 20px 0;
            padding: 20px;
            background-color: #f9f9f9;
            border-radius: 8px;
        }}
        .stat-item {{
            text-align: center;
        }}
        .stat-number {{
            font-size: 2em;
            font-weight: bold;
            color: #1e88e5;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🤖 Multi-Agent System - Architektura</h1>
        
        <div class="graph-container">
            <div class="mermaid">
{mermaid_code}
            </div>
        </div>
        
        <div class="stats">
            <div class="stat-item">
                <div class="stat-number">6</div>
                <div>Węzły</div>
            </div>
            <div class="stat-item">
                <div class="stat-number">14</div>
                <div>Krawędzie</div>
            </div>
            <div class="stat-item">
                <div class="stat-number">4</div>
                <div>Agenty</div>
            </div>
        </div>
        
        <div style="margin-top: 30px;">
            <h3>Opis architektury:</h3>
            <ul>
                <li><strong>👔 Supervisor</strong> - Zarządza przepływem zadań i routing</li>
                <li><strong>🗄️ SQL Agent</strong> - Dostęp do bazy danych logów sieciowych</li>
                <li><strong>📊 Data Analyst</strong> - Analiza danych i tworzenie statystyk</li>
                <li><strong>📝 Report Writer</strong> - Generowanie raportów końcowych</li>
            </ul>
        </div>
    </div>
    
    <script>
        mermaid.initialize({{
            startOnLoad: true,
            theme: 'default',
            flowchart: {{ 
                useMaxWidth: true,
                htmlLabels: true,
                curve: 'basis'
            }},
            securityLevel: 'loose'
        }});
    </script>
</body>
</html>"""
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(html_template)
        
        return filename