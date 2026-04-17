import sqlite3

conn = sqlite3.connect('database.db')
cursor = conn.cursor()

cursor.execute('''
    CREATE TABLE IF NOT EXISTS disease_reports (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        farmer_name TEXT,
        disease_name TEXT,
        latitude REAL,
        longitude REAL,
        image_path TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )
''')

conn.commit()
conn.close()
print("Table created!")