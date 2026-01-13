import os
import subprocess
import sys
import time
from datetime import datetime, timedelta
import psycopg2
from psycopg2 import sql

# Copied from producer to connect to the database
DB_NAME = "office_db"
DB_USER = "postgres"
DB_PASSWORD = "postgrespw"
DB_HOST = "localhost"
DB_PORT = 5432

conn = psycopg2.connect(
    dbname=DB_NAME,
    user=DB_USER,
    password=DB_PASSWORD,
    host=DB_HOST,
    port=DB_PORT
)
cursor = conn.cursor()

# -------------------------
# Periodically compute average over last 10 minutes
# -------------------------
try:
    while True:
        ten_minutes_ago = datetime.now() - timedelta(minutes=10)
        ## Fetch the data from the choosen source (to be implemented)
        cursor.execute(sql.SQL("SELECT AVG(temperature) FROM temperature_readings WHERE recorded_at >= %s"), [ten_minutes_ago])
        result = cursor.fetchone()

        avg_temp = result[0] ## replace with actual values
        if avg_temp is not None:
            print(f"{datetime.now()} - Average temperature last 10 minutes: {avg_temp:.2f} °C")
        else:
            print(f"{datetime.now()} - No data in last 10 minutes.")
        time.sleep(600)  # every 10 minutes
except KeyboardInterrupt:
    print("Stopped consuming data.")
finally:
    print("Exiting.")
    cursor.close()
    conn.close()
