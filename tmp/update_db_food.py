import sqlite3
import os

db_path = r"d:\ATP(clonned)\Smart-trip-planner\instance\air_trip_planner.db"
if not os.path.exists(db_path):
    print(f"DB not found at {db_path}")
    exit(1)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Check and add columns
cursor.execute("PRAGMA table_info(trips)")
columns = [col[1] for col in cursor.fetchall()]

modified = False
if "food_deep_dive_json" not in columns:
    print("Adding 'food_deep_dive_json' column...")
    cursor.execute("ALTER TABLE trips ADD COLUMN food_deep_dive_json TEXT DEFAULT '[]'")
    modified = True

if modified:
    conn.commit()
    print("Database updated successfully.")
else:
    print("Column already exists.")

conn.close()
