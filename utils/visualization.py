"""
Wizualizacja grafu multi-agentowego - poprawiona wersja
"""
import streamlit as st
from typing import Dict, Any
import json


class GraphVisualizer:
    """Klasa do wizualizacji grafu agentów"""
    
    def __init__(self):
        self.agent_colors = {
            "supervisor": "#ff6b6b",
            "sql_agent": "#4ecdc4", 
            "analyst": "#45b7d1",
            "report_writer": "#96ceb4",
            "start": "#ffa07a",
            "end_node": "#dda0dd"
        }
    
    def generate_mermaid_code(self, compiled_graph) -> str:
        """Generuj kod Mermaid dla grafu z debugowaniem"""
        
        # Debugowanie - sprawdź czy graf istnieje
        if not compiled_graph:
            st.error("🚨 Graf jest None")
            return self._get_fallback_mermaid()
        
        try:
            # Sprawdź czy graf ma metodę get_graph()
            if not hasattr(compiled_graph, 'get_graph'):
                st.warning("⚠️ Graf nie ma metody get_graph()")
                return self._get_fallback_mermaid()
            
            graph_info = compiled_graph.get_graph()
            st.info(f"🔍 Graf info: {type(graph_info)}")
            
            # Debugowanie - sprawdź zawartośćdd
            if hasattr(graph_info, 'nodes'):
                st.info(f"🔍 Węzły: {list(graph_info.nodes.keys())}")
            else:
                st.error("🚨 Graf nie ma atrybutu 'nodes'")
                return self._get_fallback_mermaid()
                
            if hasattr(graph_info, 'edges'):
                st.info(f"🔍 Krawędzie: {len(graph_info.edges)}")
            else:
                st.error("🚨 Graf nie ma atrybutu 'edges'")
                return self._get_fallback_mermaid()
                
        except Exception as e:
            st.error(f"🚨 Błąd get_graph(): {e}")
            return self._get_fallback_mermaid()
        
        # Generuj kod Mermaid
        mermaid_code = "graph TD\n"
        
        # Dodaj węzły
        for node_id in graph_info.nodes:
            if node_id == '__start__':
                mermaid_code += "    start([🚀 START])\n"
            elif node_id == '__end__':
                mermaid_code += "    end_node([🏁 END])\n"
            else:
                display_name = self._get_display_name(node_id)
                emoji = self._get_agent_emoji(node_id)
                mermaid_code += f"    {node_id}[\"{emoji} {display_name}\"]\n"
        
        # Dodaj krawędzie
        for edge in graph_info.edges:
            source = 'start' if edge.source == '__start__' else edge.source
            target = 'end_node' if edge.target == '__end__' else edge.target
            
            if source and target:
                mermaid_code += f"    {source} --> {target}\n"
        
        # Dodaj style
        mermaid_code += self._generate_styles()
        
        # Debugowanie - pokaż wygenerowany kod
        st.code(mermaid_code, language="text")
        
        return mermaid_code
    
    def _get_fallback_mermaid(self) -> str:
        """Fallback diagram gdy nie można wygenerować z grafu"""
        return """graph TD
    start([🚀 START])
    supervisor["👔 Supervisor"]
    sql_agent["🗄️ SQL Agent"]
    analyst["📊 Data Analyst"]
    report_writer["📝 Report Writer"]
    end_node([🏁 END])
    
    start --> supervisor
    supervisor --> sql_agent
    sql_agent --> analyst
    analyst --> report_writer
    report_writer --> end_node
    
    %% Style węzłów
    style start fill:#ffa07a,stroke:#333,color:white,stroke-width:2px
    style supervisor fill:#ff6b6b,stroke:#333,color:white,stroke-width:2px
    style sql_agent fill:#4ecdc4,stroke:#333,color:white,stroke-width:2px
    style analyst fill:#45b7d1,stroke:#333,color:white,stroke-width:2px
    style report_writer fill:#96ceb4,stroke:#333,color:white,stroke-width:2px
    style end_node fill:#dda0dd,stroke:#333,color:white,stroke-width:2px"""
    
    def _get_display_name(self, node_id: str) -> str:
        """Pobierz czytelną nazwę węzła"""
        names = {
            "supervisor": "Supervisor",
            "sql_agent": "SQL Agent", 
            "analyst": "Data Analyst",
            "report_writer": "Report Writer"
        }
        return names.get(node_id, node_id.replace('_', ' ').title())
    
    def _get_agent_emoji(self, node_id: str) -> str:
        """Pobierz emoji dla agenta"""
        emojis = {
            "supervisor": "👔",
            "sql_agent": "🗄️",
            "analyst": "📊", 
            "report_writer": "📝"
        }
        return emojis.get(node_id, "🤖")
    
    def _generate_styles(self) -> str:
        """Generuj style CSS dla węzłów"""
        styles = "\n    %% Style węzłów\n"
        for node, color in self.agent_colors.items():
            styles += f"    style {node} fill:{color},stroke:#333,color:white,stroke-width:2px\n"
        return styles
    
    def show_in_streamlit(self, compiled_graph, title="🔄 Graf przepływu agentów"):
        """Wyświetl graf w Streamlit z ulepszoną obsługą"""
        st.markdown(f"### {title}")
        
        # Generuj kod Mermaid
        mermaid_code = self.generate_mermaid_code(compiled_graph)
        
        # Spróbuj renderować z Mermaid
        try:
            self._render_mermaid(mermaid_code)
        except Exception as e:
            st.error(f"Błąd renderowania Mermaid: {e}")
            # Fallback do prostego HTML
            self._render_simple_html(mermaid_code)
    
    def _render_mermaid(self, mermaid_code: str):
        """Renderuj z użyciem Mermaid"""
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
                .error {{
                    color: red;
                    text-align: center;
                    padding: 20px;
                }}
            </style>
        </head>
        <body>
            <div id="mermaid-container">
                <div class="mermaid">
{mermaid_code}
                </div>
            </div>
            
            <script>
                try {{
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
                }} catch (error) {{
                    document.getElementById('mermaid-container').innerHTML = 
                        '<div class="error">Błąd ładowania Mermaid: ' + error.message + '</div>';
                }}
            </script>
        </body>
        </html>
        """
        
        st.components.v1.html(mermaid_html, height=500, scrolling=True)
    
    def _render_simple_html(self, mermaid_code: str):
        """Fallback do prostego HTML bez Mermaid"""
        st.markdown("**Fallback - prosty diagram:**")
        
        html = """
        <div style="text-align: center; padding: 20px; border: 1px solid #ddd; border-radius: 8px;">
            <div style="margin: 10px;">🚀 START</div>
            <div style="margin: 10px;">↓</div>
            <div style="margin: 10px; padding: 10px; background: #ff6b6b; color: white; border-radius: 5px;">👔 Supervisor</div>
            <div style="margin: 10px;">↓</div>
            <div style="margin: 10px; padding: 10px; background: #4ecdc4; color: white; border-radius: 5px;">🗄️ SQL Agent</div>
            <div style="margin: 10px;">↓</div>
            <div style="margin: 10px; padding: 10px; background: #45b7d1; color: white; border-radius: 5px;">📊 Data Analyst</div>
            <div style="margin: 10px;">↓</div>
            <div style="margin: 10px; padding: 10px; background: #96ceb4; color: white; border-radius: 5px;">📝 Report Writer</div>
            <div style="margin: 10px;">↓</div>
            <div style="margin: 10px;">🏁 END</div>
        </div>
        """
        
        st.markdown(html, unsafe_allow_html=True)
    
    def get_graph_stats(self, compiled_graph) -> Dict[str, Any]:
        """Pobierz statystyki grafu"""
        try:
            if not compiled_graph or not hasattr(compiled_graph, 'get_graph'):
                return {
                    "total_nodes": 5,
                    "total_edges": 4,
                    "nodes": ["supervisor", "sql_agent", "analyst", "report_writer"],
                    "agent_count": 4,
                    "status": "fallback"
                }
            
            graph_info = compiled_graph.get_graph()
            
            return {
                "total_nodes": len(graph_info.nodes),
                "total_edges": len(graph_info.edges),
                "nodes": list(graph_info.nodes.keys()),
                "agent_count": len([n for n in graph_info.nodes.keys() if not n.startswith('__')]),
                "status": "active"
            }
        except Exception as e:
            return {
                "total_nodes": 0,
                "total_edges": 0,
                "nodes": [],
                "agent_count": 0,
                "status": f"error: {e}"
            }