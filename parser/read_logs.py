import sqlite3

def main():
    conn = sqlite3.connect("logs.db")
    cursor = conn.cursor()

    # Pobierz nazwy kolumn z tabeli logs
    cursor.execute("PRAGMA table_info(logs)")
    columns = [info[1] for info in cursor.fetchall()]

    # Wyświetl nagłówki kolumn
    print(", ".join(columns))

    # Pobierz wszystkie dane z tabeli logs
    cursor.execute("SELECT * FROM logs")
    rows = cursor.fetchall()

    # Wyświetl dane w formacie CSV
    for row in rows:
        print(", ".join(map(str, row)))

    conn.close()

if __name__ == "__main__":
    main()