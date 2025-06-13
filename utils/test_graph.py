"""
Test wizualizacji grafu - uruchom to aby sprawdzić czy graf działa
"""
import streamlit as st
from utils.visualization import GraphVisualizer

def test_mermaid_standalone():
    """Test samodzielnej wizualizacji Mermaid"""
    st.title("🧪 Test wizualizacji grafu")
    
    # Test 1: Prosty Mermaid bez grafu
    st.header("Test 1: Statyczny diagram Mermaid")
    
    visualizer = GraphVisualizer()
    
    # Użyj fallback diagram
    mermaid_code = visualizer._get_fallback_mermaid()
    
    mermaid_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <script src="https://cdn.jsdelivr.net/npm/mermaid@10.6.1/dist/mermaid.min.js"></script>
        <style>
            body {{ 
                font-family: Arial, sans-serif;
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
                    htmlLabels: true
                }},
                securityLevel: 'loose'
            }});
        </script>
    </body>
    </html>
    """
    
    st.components.v1.html(mermaid_html, height=500)
    
    # Test 2: Pokaż kod Mermaid
    st.header("Test 2: Kod Mermaid")
    st.code(mermaid_code, language="text")
    
    # Test 3: Fallback HTML
    st.header("Test 3: Fallback HTML")
    visualizer._render_simple_html(mermaid_code)
    
    # Test 4: Sprawdź system
    st.header("Test 4: Sprawdzenie systemu")
    
    try:
        from langgraph_multi_agent import MultiAgentSystem
        system = MultiAgentSystem()
        
        if system and hasattr(system, 'graph'):
            st.success("✅ System załadowany, graf dostępny")
            visualizer.show_in_streamlit(system.graph, "Graf systemu")
        else:
            st.warning("⚠️ System bez grafu")
            
    except Exception as e:
        st.error(f"❌ Błąd systemu: {e}")

if __name__ == "__main__":
    test_mermaid_standalone()