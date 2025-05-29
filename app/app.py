import streamlit as st
import pandas as pd
import altair as alt
import sqlite3
import os
from datetime import datetime, timedelta

# 🔌 Połączenie z bazą SQLite
DB_PATH = os.getenv("DB_PATH", "parser/logs.db")

def get_connection():
    return sqlite3.connect(DB_PATH)

st.set_page_config(layout="wide")
st.title("📊 Analiza logów aplikacji (SQLite + Streamlit)")

# 📋 Filtry boczne
with st.sidebar:
    st.header("🔍 Filtry")

    conn = get_connection()
    srcips = ["(wszystkie)"] + sorted(
        [row[0] for row in conn.execute("SELECT DISTINCT srcip FROM logs WHERE srcip IS NOT NULL")]
    )
    appcats = ["(wszystkie)"] + sorted(
        [row[0] for row in conn.execute("SELECT DISTINCT appcat FROM logs WHERE appcat IS NOT NULL")]
    )
    apps = ["(wszystkie)"] + sorted(
        [row[0] for row in conn.execute("SELECT DISTINCT app FROM logs WHERE app IS NOT NULL")]
    )
    actions = ["(wszystkie)"] + sorted(
        [row[0] for row in conn.execute("SELECT DISTINCT action FROM logs WHERE action IS NOT NULL")]
    )
    services = ["(wszystkie)"] + sorted(
        [row[0] for row in conn.execute("SELECT DISTINCT service FROM logs WHERE service IS NOT NULL")]
    )

    selected_srcip = st.selectbox("📍 Źródłowy IP (srcip):", srcips)
    selected_appcat = st.selectbox("📂 Kategoria aplikacji (appcat):", appcats)
    selected_app = st.selectbox("🧩 Aplikacja (app):", apps)
    selected_action = st.selectbox("🚦 Działanie (action):", actions)
    selected_service = st.selectbox("🔧 Usługa (service):", services)

    min_row = conn.execute(
        "SELECT date || ' ' || time FROM logs ORDER BY date || ' ' || time ASC LIMIT 1"
    ).fetchone()
    max_row = conn.execute(
        "SELECT date || ' ' || time FROM logs ORDER BY date || ' ' || time DESC LIMIT 1"
    ).fetchone()
    if min_row and max_row:
        min_date = datetime.strptime(min_row[0], "%Y-%m-%d %H:%M:%S")
        max_date = datetime.strptime(max_row[0], "%Y-%m-%d %H:%M:%S")
        start_time, end_time = st.slider(
            "⏱ Zakres czasu (timestamp):",
            value=(min_date, max_date),
            format="YYYY-MM-DD HH:mm",
            step=timedelta(minutes=1),
        )
    else:
        start_time, end_time = None, None

    conn.close()

    max_records = st.slider(
        "📦 Maks. liczba rekordów:", min_value=100, max_value=5000, value=1000, step=100
    )

# 📡 Dynamiczne zapytanie do SQLite
sql = "SELECT * FROM logs WHERE 1=1"
params = []
if start_time and end_time:
    sql += " AND datetime(date || ' ' || time) BETWEEN ? AND ?"
    params.extend([
        start_time.strftime("%Y-%m-%d %H:%M:%S"),
        end_time.strftime("%Y-%m-%d %H:%M:%S"),
    ])
if selected_srcip != "(wszystkie)":
    sql += " AND srcip = ?"
    params.append(selected_srcip)
if selected_appcat != "(wszystkie)":
    sql += " AND appcat = ?"
    params.append(selected_appcat)
if selected_app != "(wszystkie)":
    sql += " AND app = ?"
    params.append(selected_app)
if selected_action != "(wszystkie)":
    sql += " AND action = ?"
    params.append(selected_action)
if selected_service != "(wszystkie)":
    sql += " AND service = ?"
    params.append(selected_service)
sql += " LIMIT ?"
params.append(max_records)

with st.spinner("📡 Pobieranie danych..."):
    conn = get_connection()
    data = pd.read_sql_query(sql, conn, params=params)
    conn.close()
    if not data.empty:
        data["timestamp"] = pd.to_datetime(data["date"] + " " + data["time"])

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