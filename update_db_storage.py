
import sqlite3
import json
import os
from config import get_config

# Get config
config = get_config()

# Determine paths based on OS
if os.name == "nt":
    db_path = config.get("WindowsPaths", "sqlite_path")
    storage_path = config.get("WindowsPaths", "storage_path")
elif os.name == "posix":
    if os.uname().sysname == "Darwin":
        db_path = config.get("MacPaths", "sqlite_path")
        storage_path = config.get("MacPaths", "storage_path")
    else:
        db_path = config.get("LinuxPaths", "sqlite_path")
        storage_path = config.get("LinuxPaths", "storage_path")

print("DB path:", db_path)
print("Storage path:", storage_path)

# Update SQLite DB
conn = sqlite3.connect(db_path)
cursor = conn.cursor()
updates = [
    ("cursorAuth/stripeMembershipType", "pro"),
    ("cursorAuth/stripeSubscriptionStatus", "active"),
]
for key, value in updates:
    cursor.execute("SELECT COUNT(*) FROM ItemTable WHERE key = ?", (key,))
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO ItemTable (key, value) VALUES (?, ?)", (key, value))
    else:
        cursor.execute("UPDATE ItemTable SET value = ? WHERE key = ?", (value, key))
    print(f"Updated DB: {key} = {value}")
conn.commit()
conn.close()

# Update storage.json
data = {}
if os.path.exists(storage_path):
    with open(storage_path, "r", encoding="utf-8") as f:
        data = json.load(f)
for key, value in updates:
    data[key] = value
    print(f"Updated storage.json: {key} = {value}")
with open(storage_path, "w", encoding="utf-8") as f:
    json.dump(data, f, indent=4)

print("Done!")
