import sqlite3
import os

db_path = r"d:\ATP(clonned)\Smart-trip-planner\instance\trip_planner.db"
if not os.path.exists(db_path):
    print(f"DB not found at {db_path}")
    exit(1)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Check and add columns
cursor.execute("PRAGMA table_info(itineraries)")
columns = [col[1] for col in cursor.fetchall()]

modified = False
if "latitude" not in columns:
    print("Adding 'latitude' column...")
    cursor.execute("ALTER TABLE itineraries ADD COLUMN latitude FLOAT")
    modified = True
if "longitude" not in columns:
    print("Adding 'longitude' column...")
    cursor.execute("ALTER TABLE itineraries ADD COLUMN longitude FLOAT")
    modified = True

if modified:
    conn.commit()
    print("Database updated successfully.")
else:
    print("Columns already exist.")

conn.close()
