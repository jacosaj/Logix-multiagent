"""
Najprostszy test Mermaid w Streamlit
Uruchom: streamlit run simple_mermaid_test.py
"""
import streamlit as st

st.title("🧪 Prosty test Mermaid")

# Bardzo podstawowy diagram
basic_mermaid = """
graph TD
    A[Start] --> B[Process]
    B --> C[End]
    
    style A fill:#ff9999
    style B fill:#99ccff  
    style C fill:#99ff99
"""

# HTML z Mermaid
html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <script src="https://cdn.jsdelivr.net/npm/mermaid@10.6.1/dist/mermaid.min.js"></script>
</head>
<body>
    <div class="mermaid">
{basic_mermaid}
    </div>
    
    <script>
        mermaid.initialize({{startOnLoad:true}});
    </script>
</body>
</html>
"""

st.markdown("### Test 1: Podstawowy Mermaid")
st.components.v1.html(html_content, height=300)

st.markdown("### Test 2: Kod diagramu")
st.code(basic_mermaid)

st.markdown("### Test 3: Informacje o przeglądarce")
st.write("Jeśli powyżej nie ma diagramu, sprawdź:")
st.write("1. Czy masz włączony JavaScript")
st.write("2. Czy nie blokujesz zewnętrznych skryptów")
st.write("3. Czy w konsoli przeglądarki (F12) są błędy")

# Test alternatywny z lokalnym Mermaid
st.markdown("### Test 4: Alternatywny Mermaid")

alt_html = """
<div id="mermaid-div">Ładowanie...</div>

<script type="module">
  import mermaid from 'https://cdn.skypack.dev/mermaid@9';
  
  mermaid.initialize({startOnLoad: true});
  
  const element = document.getElementById('mermaid-div');
  const graphDefinition = `graph TD
    A[Start] --> B[Process]
    B --> C[End]`;
    
  try {
    const {svg} = await mermaid.render('graph1', graphDefinition);
    element.innerHTML = svg;
  } catch (error) {
    element.innerHTML = 'Błąd: ' + error.message;
  }
</script>
"""

st.components.v1.html(alt_html, height=300)