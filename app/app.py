import streamlit as st
import pandas as pd
import altair as alt
import sqlite3
import os
from datetime import datetime, timedelta

# 🔌 Połączenie z bazą SQLite (z .env)
DB_PATH = os.getenv("DB_PATH", "db/logs.db")
conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row

st.set_page_config(layout="wide")
st.title("📊 Analiza logów aplikacji (SQLite + Streamlit)")

# 📋 Filtry boczne
with st.sidebar:
    st.header("🔍 Filtry")

    def distinct(column):
        rows = conn.execute(f"SELECT DISTINCT {column} FROM logs_selected").fetchall()
        return sorted([r[0] for r in rows if r[0] is not None])

    srcips = ["(wszystkie)"] + distinct("srcip")
    appcats = ["(wszystkie)"] + distinct("appcat")
    apps = ["(wszystkie)"] + distinct("app")
    actions = ["(wszystkie)"] + distinct("action")
    services = ["(wszystkie)"] + distinct("service")

    selected_srcip = st.selectbox("📍 Źródłowy IP (srcip):", srcips)
    selected_appcat = st.selectbox("📂 Kategoria aplikacji (appcat):", appcats)
    selected_app = st.selectbox("🧩 Aplikacja (app):", apps)
    selected_action = st.selectbox("🚦 Działanie (action):", actions)
    selected_service = st.selectbox("🔧 Usługa (service):", services)

    cur = conn.execute("SELECT MIN(timestamp), MAX(timestamp) FROM logs_selected")
    min_ts, max_ts = cur.fetchone()
    if min_ts and max_ts:
        min_date = pd.to_datetime(min_ts).to_pydatetime()
        max_date = pd.to_datetime(max_ts).to_pydatetime()
        start_time, end_time = st.slider("⏱ Zakres czasu (timestamp):",
                                         value=(min_date, max_date),
                                         format="YYYY-MM-DD HH:mm",
                                         step=timedelta(minutes=1))
    else:
        start_time, end_time = None, None

    max_records = st.slider("📦 Maks. liczba rekordów:", min_value=100, max_value=5000, value=1000, step=100)

# 📡 Dynamiczne zapytanie do SQLite
query = "SELECT * FROM logs_selected WHERE 1=1"
params = {}
if start_time and end_time:
    query += " AND timestamp BETWEEN :start_time AND :end_time"
    params["start_time"] = start_time
    params["end_time"] = end_time
if selected_srcip != "(wszystkie)":
    query += " AND srcip = :srcip"
    params["srcip"] = selected_srcip
if selected_appcat != "(wszystkie)":
    query += " AND appcat = :appcat"
    params["appcat"] = selected_appcat
if selected_app != "(wszystkie)":
    query += " AND app = :app"
    params["app"] = selected_app
if selected_action != "(wszystkie)":
    query += " AND action = :action"
    params["action"] = selected_action
if selected_service != "(wszystkie)":
    query += " AND service = :service"
    params["service"] = selected_service
query += " LIMIT :limit"
params["limit"] = max_records

with st.spinner("📡 Pobieranie danych..."):
    data = pd.read_sql_query(query, conn, params=params, parse_dates=["timestamp"]) 

if data.empty:
    st.warning("Brak danych do wyświetlenia.")
    st.stop()

# 📄 Tabela wyników
st.subheader(f"Wyniki: {len(data)} rekordów")
st.dataframe(data, use_container_width=True)

# 📈 Statystyki

def format_bytes(num):
    if num >= 1_000_000_000:
        return f"{num / 1_000_000_000:.2f} GB"
    elif num >= 1_000_000:
        return f"{num / 1_000_000:.2f} MB"
    else:
        return f"{num / 1_000:.2f} KB"

col1, col2 = st.columns(2)
if "sentbyte" in data.columns:
    col1.metric("📤 Wysłane dane", format_bytes(data["sentbyte"].sum()))
if "rcvdbyte" in data.columns:
    col2.metric("📥 Otrzymane dane", format_bytes(data["rcvdbyte"].sum()))

# 📊 Wykresy
st.subheader("📊 Wykresy")

if "appcat" in data.columns and "sentbyte" in data.columns:
    chart1 = alt.Chart(data).mark_bar().encode(
        x=alt.X('sum(sentbyte):Q', title='Suma wysłanych bajtów'),
        y=alt.Y('appcat:N', sort='-x'),
        color='appcat:N'
    ).properties(title="📦 Wysłane bajty wg kategorii aplikacji", height=300)
    st.altair_chart(chart1, use_container_width=True)

if "app" in data.columns and "sentbyte" in data.columns:
    chart2 = alt.Chart(data).mark_bar().encode(
        x=alt.X('sum(sentbyte):Q', title='Wysłane bajty'),
        y=alt.Y('app:N', sort='-x'),
        tooltip=['app', 'sum(sentbyte)'],
        color='app:N'
    ).properties(title="🔥 Top aplikacje wg ruchu", height=300)
    st.altair_chart(chart2, use_container_width=True)

if "timestamp" in data.columns:
    df_time = data.copy()
    df_time["minuta"] = pd.to_datetime(df_time["timestamp"]).dt.floor("min")
    chart3 = alt.Chart(df_time).mark_line().encode(
        x='minuta:T',
        y='sum(sentbyte):Q',
        tooltip=['minuta:T', 'sum(sentbyte):Q']
    ).properties(title="📈 Ruch wysyłany w czasie", height=300)
    st.altair_chart(chart3, use_container_width=True)
