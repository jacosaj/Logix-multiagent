import re
import os
import sqlite3
from dateutil import parser as date_parser
from concurrent.futures import ThreadPoolExecutor, as_completed

# 🔐 Zmienne środowiskowe (.env → docker-compose)
DB_PATH = os.getenv("DB_PATH", "db/logs.db")

# Ensure database and table exist
INIT_CONN = sqlite3.connect(DB_PATH)
INIT_CURSOR = INIT_CONN.cursor()
columns = (
    "date TEXT", "time TEXT", "eventtime TEXT", "logid TEXT",
    "srcip TEXT", "srcname TEXT", "srcport TEXT",
    "dstip TEXT", "dstport TEXT", "proto TEXT",
    "action TEXT", "policyname TEXT", "service TEXT", "transport TEXT",
    "appid TEXT", "app TEXT", "appcat TEXT", "apprisk TEXT",
    "duration TEXT", "sentbyte TEXT", "rcvdbyte TEXT",
    "sentpkt TEXT", "rcvdpkt TEXT", "shapersentname TEXT",
    "osname TEXT", "mastersrcmac TEXT", "timestamp TEXT"
)
INIT_CURSOR.execute(
    f"CREATE TABLE IF NOT EXISTS logs_selected ({', '.join(columns)})"
)
INIT_CONN.commit()
INIT_CONN.close()

# 🔎 Lista dozwolonych kategorii appcat
ALLOWED_APPCATS = {"Social.Media", "Video.Audio", "Game", "Adult"}

# 🔑 Lista kolumn do wyciągania
LOG_FIELDS = [
    "date", "time", "eventtime", "logid",
    "srcip", "srcname", "srcport",
    "dstip", "dstport", "proto",
    "action", "policyname", "service", "transport",
    "appid", "app", "appcat", "apprisk",
    "duration", "sentbyte", "rcvdbyte",
    "sentpkt", "rcvdpkt", "shapersentname",
    "osname", "mastersrcmac"
]

BATCH_SIZE = 1000
THREADS = os.cpu_count() or 4

def try_convert(value):
    if value.isdigit():
        return int(value)
    try:
        return float(value)
    except:
        return value

def parse_line(line):
    pattern = r'(\w+)=("[^"]*"|\S+)'
    matches = re.findall(pattern, line)
    doc = {}
    for key, value in matches:
        if key in LOG_FIELDS:
            clean = value.strip('"')
            doc[key] = try_convert(clean)

    if "appcat" not in doc or doc["appcat"] not in ALLOWED_APPCATS:
        return None

    if "date" in doc and "time" in doc:
        try:
            doc["timestamp"] = date_parser.parse(f"{doc['date']} {doc['time']}")
        except:
            pass
    return doc

def process_batch(batch):
    docs = [parse_line(line) for line in batch]
    docs = [doc for doc in docs if doc is not None]
    if docs:
        conn = sqlite3.connect(DB_PATH)
        placeholders = ','.join(['?'] * (len(LOG_FIELDS) + 1))
        columns = LOG_FIELDS + ["timestamp"]
        values = [[doc.get(col) for col in columns] for doc in docs]
        conn.executemany(
            f"INSERT INTO logs_selected ({', '.join(columns)}) VALUES ({placeholders})",
            values,
        )
        conn.commit()
        conn.close()

def load_log_file(filepath):
    with open(filepath, "r") as f:
        batch = []
        futures = []

        with ThreadPoolExecutor(max_workers=THREADS) as executor:
            for i, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                batch.append(line)
                if len(batch) >= BATCH_SIZE:
                    futures.append(executor.submit(process_batch, batch.copy()))
                    batch.clear()

            if batch:
                futures.append(executor.submit(process_batch, batch.copy()))

            for future in as_completed(futures):
                future.result()

    print("✅ Parser zakończył działanie.")

# 🔁 Główne wejście
if __name__ == "__main__":
    load_log_file("logs/bigfile.log")
