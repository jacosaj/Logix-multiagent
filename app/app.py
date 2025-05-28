import streamlit as st
import pandas as pd
import altair as alt
from pymongo import MongoClient
import os
from datetime import datetime, timedelta

# 🔌 Połączenie z MongoDB (z .env)
client = MongoClient(os.getenv("MONGO_URI", "mongodb://mongodb:27017/"))
db = client["logdb"]
collection = db["logs_selected"]

st.set_page_config(layout="wide")
st.title("📊 Analiza logów aplikacji (MongoDB + Streamlit)")

# 📋 Filtry boczne
with st.sidebar:
    st.header("🔍 Filtry")

    srcips = ["(wszystkie)"] + sorted(collection.distinct("srcip"))
    appcats = ["(wszystkie)"] + sorted(collection.distinct("appcat"))
    apps = ["(wszystkie)"] + sorted(collection.distinct("app"))
    actions = ["(wszystkie)"] + sorted(collection.distinct("action"))
    services = ["(wszystkie)"] + sorted(collection.distinct("service"))

    selected_srcip = st.selectbox("📍 Źródłowy IP (srcip):", srcips)
    selected_appcat = st.selectbox("📂 Kategoria aplikacji (appcat):", appcats)
    selected_app = st.selectbox("🧩 Aplikacja (app):", apps)
    selected_action = st.selectbox("🚦 Działanie (action):", actions)
    selected_service = st.selectbox("🔧 Usługa (service):", services)

    min_doc = collection.find_one(sort=[("timestamp", 1)])
    max_doc = collection.find_one(sort=[("timestamp", -1)])
    if min_doc and max_doc:
        min_date = pd.to_datetime(min_doc["timestamp"]).to_pydatetime()
        max_date = pd.to_datetime(max_doc["timestamp"]).to_pydatetime()
        start_time, end_time = st.slider("⏱ Zakres czasu (timestamp):",
                                         value=(min_date, max_date),
                                         format="YYYY-MM-DD HH:mm",
                                         step=timedelta(minutes=1))
    else:
        start_time, end_time = None, None

    max_records = st.slider("📦 Maks. liczba rekordów:", min_value=100, max_value=5000, value=1000, step=100)

# 📡 Dynamiczne zapytanie do MongoDB
query = {}
if start_time and end_time:
    query["timestamp"] = {"$gte": start_time, "$lte": end_time}
if selected_srcip != "(wszystkie)": query["srcip"] = selected_srcip
if selected_appcat != "(wszystkie)": query["appcat"] = selected_appcat
if selected_app != "(wszystkie)": query["app"] = selected_app
if selected_action != "(wszystkie)": query["action"] = selected_action
if selected_service != "(wszystkie)": query["service"] = selected_service

with st.spinner("📡 Pobieranie danych..."):
    cursor = collection.find(query, {"_id": 0}).limit(max_records)
    data = pd.DataFrame(list(cursor))

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