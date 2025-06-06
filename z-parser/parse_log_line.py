import sqlite3
import csv

# Nazwa pliku bazy i pliku CSV
DB_FILE = 'logs.db'
CSV_FILE = 'logi_filtrowane.csv'

# Połączenie z bazą
conn = sqlite3.connect(DB_FILE)
c = conn.cursor()

# Tworzenie tabeli (jeśli nie istnieje)
c.execute('''
CREATE TABLE IF NOT EXISTS logs (
    date TEXT,
    time TEXT,
    eventtime TEXT,
    logid TEXT,
    srcip TEXT,
    srcname TEXT,
    srcport INTEGER,
    dstip TEXT,
    dstport INTEGER,
    proto INTEGER,
    action TEXT,
    policyname TEXT,
    service TEXT,
    transport TEXT,
    appid TEXT,
    app TEXT,
    appcat TEXT,
    apprisk TEXT,
    duration INTEGER,
    sentbyte INTEGER,
    rcvdbyte INTEGER,
    sentpkt INTEGER,
    rcvdpkt INTEGER,
    shapersentname TEXT,
    osname TEXT,
    mastersrcmac TEXT
)
''')

# Wczytywanie CSV i wrzucanie do bazy
with open(CSV_FILE, newline='', encoding='utf-8') as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
        # Zamień puste stringi na None (NULL w SQLite)
        values = [row[col] if row[col] != '' else None for col in reader.fieldnames]
        c.execute(f'''
            INSERT INTO logs ({','.join(reader.fieldnames)})
            VALUES ({','.join(['?']*len(reader.fieldnames))})
        ''', values)

conn.commit()
conn.close()

print("Import zakończony!")