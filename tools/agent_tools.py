"""
Narzędzia dla agentów - funkcje transferu między agentami
"""
from langchain_core.tools import tool


@tool
def transfer_to_sql_agent():
    """Przekaż zadanie do SQL Agenta gdy potrzebne są dane z bazy"""
    return "Przekazuję do SQL Agenta..."


@tool 
def transfer_to_analyst():
    """Przekaż zadanie do Data Analyst gdy potrzebna jest analiza danych"""
    return "Przekazuję do Data Analyst..."


@tool
def transfer_to_report_writer():
    """Przekaż zadanie do Report Writer gdy potrzebny jest raport"""
    return "Przekazuję do Report Writer..."


@tool
def transfer_to_supervisor():
    """Wróć do supervisora gdy zadanie jest ukończone lub potrzebna jest decyzja"""
    return "Wracam do supervisora..."


# Lista wszystkich narzędzi
ALL_TOOLS = [
    transfer_to_sql_agent,
    transfer_to_analyst,
    transfer_to_report_writer,
    transfer_to_supervisor
]
