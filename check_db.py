import sqlite3
conn = sqlite3.connect('database.db')
cursor = conn.cursor()
cursor.execute('SELECT * FROM disease_reports')
print(cursor.fetchall())
conn.close()