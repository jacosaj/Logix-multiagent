import re
import os
from pymongo import MongoClient
from dateutil import parser as date_parser
from concurrent.futures import ThreadPoolExecutor, as_completed

# 🔐 Zmienne środowiskowe (.env → docker-compose)
MONGO_URI = os.getenv("MONGO_URI", "mongodb://mongodb:27017/")
client = MongoClient(MONGO_URI)
db = client["logdb"]
collection = db["logs_selected"]

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
        collection.insert_many(docs)

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
