import sqlite3
import os

db_path = r"d:\ATP(clonned)\Smart-trip-planner\instance\air_trip_planner.db"
if not os.path.exists(db_path):
    print(f"DB not found at {db_path}")
    exit(1)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Update itinerary_edit_requests
cursor.execute("PRAGMA table_info(itinerary_edit_requests)")
columns = [col[1] for col in cursor.fetchall()]

modified = False
if "proposed_latitude" not in columns:
    print("Adding 'proposed_latitude' column...")
    cursor.execute("ALTER TABLE itinerary_edit_requests ADD COLUMN proposed_latitude FLOAT")
    modified = True
if "proposed_longitude" not in columns:
    print("Adding 'proposed_longitude' column...")
    cursor.execute("ALTER TABLE itinerary_edit_requests ADD COLUMN proposed_longitude FLOAT")
    modified = True

if modified:
    conn.commit()
    print("Database updated successfully.")
else:
    print("Columns already exist.")

conn.close()
