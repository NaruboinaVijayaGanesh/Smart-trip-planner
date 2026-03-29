import sqlite3
import os

db_path = r"d:\ATP(clonned)\Smart-trip-planner\instance\trip_planner.db"

if not os.path.exists(db_path):
    # Try alternate location if not found
    db_path = r"d:\ATP(clonned)\Smart-trip-planner\app.db"

if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(itineraries)")
    columns = cursor.fetchall()
    print("Columns in 'itineraries' table:")
    for col in columns:
        print(col)
    conn.close()
else:
    print(f"Database not found at {db_path}")
