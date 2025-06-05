import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_community.utilities.sql_database import SQLDatabase
from langchain_community.agent_toolkits.sql.toolkit import SQLDatabaseToolkit
from langchain_core.tools.simple import Tool
from langgraph.graph import END, StateGraph
from langgraph.graph.message import add_messages
from langchain_core.messages import HumanMessage, AIMessage
import functools

# === Config & LLM ===
load_dotenv()
llm = ChatOpenAI(
    model_name="gpt-4o-mini",
    openai_api_key=os.environ['OPENAI_API_KEY_TEG'],
    temperature=0,
)

# === SQL DB ===
db_path = r"C:\PJATK\SEMESTR2\teg projekt\projekt\Logi-projektTEG\parser\logs.db"  # Upewnij się że ścieżka jest poprawna
sql_db = SQLDatabase.from_uri(f"sqlite:///{db_path}")
sql_toolkit = SQLDatabaseToolkit(db=sql_db, llm=llm)

# === Narzędzie czyszczące zapytania SQL ===
def clean_sql_response(response: str) -> str:
    response = response.strip()
    if response.lower().startswith("sqlquery:"):
        response = response[len("sqlquery:"):].strip()
    return response.replace("```sql", "").replace("```", "").strip()

def cleaned_sql_tool(query: str) -> str:
    cleaned_query = clean_sql_response(query)
    return sql_db.run(cleaned_query)

sql_query_tool = Tool.from_function(
    func=cleaned_sql_tool,
    name="run_clean_sql_query",
    description="Wykonuje oczyszczone zapytanie SQL."
)

# === Agent obliczający straty czasu ===
def calculate_loss(time_lost_seconds: int, avg_salary_per_hour: float = 50) -> float:
    hours = time_lost_seconds / 3600
    return round(hours * avg_salary_per_hour, 2)

time_loss_tool = Tool.from_function(
    func=calculate_loss,
    name="CalculateTimeLoss",
    description="Oblicza stratę finansową firmy na podstawie czasu straconego w sekundach."
)

# === Prompty systemowe ===
sql_prompt = """Jesteś ekspertem SQL. Zamień pytanie użytkownika na zapytanie SQL. Odpowiedz wyłącznie zapytaniem SQL, bez dodatkowych informacji, komentarzy, formatowania ani opisów."""

loss_prompt = """Dostajesz tekst zawierający liczbę sekund. Oblicz straty w złotówkach (50 PLN/h)."""

summary_prompt = """Na podstawie poprzednich wyników wygeneruj krótką odpowiedź w języku polskim."""

# === Tworzenie agentów ===
def create_agent(llm, tools, system_message):
    prompt = ChatPromptTemplate.from_messages([
        ("system", "{system_message}"),
        MessagesPlaceholder(variable_name="messages"),
    ]).partial(system_message=system_message)
    return prompt | llm.bind_tools(tools) if tools else prompt | llm

search_agent = create_agent(llm, [], sql_prompt)
loss_agent = create_agent(llm, [time_loss_tool], loss_prompt)
summary_agent = create_agent(llm, [], summary_prompt)

# === Funkcje węzłów ===
def agent_node(state, agent, name):
    print(f"[DEBUG] Running agent: {name}")
    # Usuwamy puste wiadomości
    state["messages"] = [m for m in state["messages"] if m.content.strip()]
    result = agent.invoke(state)
    return {"messages": state["messages"] + [result], "no_of_iterations": state["no_of_iterations"] + 1}

search_node = functools.partial(agent_node, agent=search_agent, name="Search Agent")
loss_node = functools.partial(agent_node, agent=loss_agent, name="Loss Agent")
summary_node = functools.partial(agent_node, agent=summary_agent, name="Summary Agent")

# === NOWY WĘZEŁ TOOL_HANDLER wykonujący SQL ===
def tool_handler_node(state, tools):
    last_message = state["messages"][-1].content
    print(f"[DEBUG] Running tools on last message: '''{last_message}'''")

    cleaned_query = clean_sql_response(last_message)

    sql_tool = next((t for t in tools if t.name == "run_clean_sql_query"), None)
    if not sql_tool:
        print("[ERROR] Nie znaleziono narzędzia do wykonania SQL.")
        result = "Brak narzędzia SQL"
    else:
        result = sql_tool.run(cleaned_query)

    new_message = AIMessage(content=str(result))
    return {
        "messages": state["messages"] + [new_message],
        "no_of_iterations": state["no_of_iterations"],
        "last_tool_result": result,
    }

# === Logika decyzyjna ===
def check_if_contains_time(state):
    content = state["messages"][-1].content.lower()
    if "sekund" in content or "godzin" in content or "czas" in content:
        return "loss"
    return "end"

def check_time_node(state):
    next_path = check_if_contains_time(state)
    return {**state, "next_path": next_path}

# === Graf LangGraph ===
workflow = StateGraph(
    state_schema=set([
        frozenset([
            ("messages", list),
            ("no_of_iterations", int),
            ("next_path", str),
        ])
    ])
)


print("StateGraph utworzony pomyślnie!")


workflow.add_node("search", search_node)
workflow.add_node("tool_handler", functools.partial(tool_handler_node, tools=[sql_query_tool, time_loss_tool]))
workflow.add_node("loss", loss_node)
workflow.add_node("summary", summary_node)
workflow.add_node("check", check_time_node)

workflow.set_entry_point("search")
workflow.add_edge("search", "tool_handler")
workflow.add_edge("tool_handler", "check")
workflow.add_conditional_edges("check", lambda s: s.get("next_path", None), {"loss": "loss", "end": END})
workflow.add_edge("loss", "summary")
workflow.add_edge("summary", END)

graph = workflow.compile()


# === Wykonanie ===
question = "Ile czasu spędził użytkownik o MAC 1e:ea:73:e5:55:b0 na Facebooku 16.05.2025?"
input_data = {"messages": [HumanMessage(content=question)], "no_of_iterations": 0}

for step, event in enumerate(graph.stream(input_data, stream_mode="values"), 1):
    print(f"\n--- KROK {step} ---")
    event["messages"][-1].pretty_print()
