# test_db_connection.py
import psycopg2
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get the DATABASE_URL from .env
db_url = os.getenv("DATABASE_URL")
print(f"Trying to connect using: {db_url}")

try:
    # Parse the connection string manually to show the components
    # Format: postgresql://username:password@host:port/dbname
    parts = db_url.replace("postgresql://", "").split("@")
    user_pass = parts[0].split(":")
    host_db = parts[1].split("/")

    username = user_pass[0]
    password = user_pass[1]
    host = host_db[0].split(":")[0]
    port = host_db[0].split(":")[1] if ":" in host_db[0] else "5432"
    dbname = host_db[1]

    print(f"Parsed connection parameters:")
    print(f"Username: {username}")
    print(f"Password: {'*' * len(password)}")
    print(f"Host: {host}")
    print(f"Port: {port}")
    print(f"Database: {dbname}")

    # Try to connect using these explicit parameters
    conn = psycopg2.connect(
        dbname=dbname,
        user=username,
        password=password,
        host=host,
        port=port
    )
    print("\nConnection successful!")

    # Verify we can execute a simple query
    cursor = conn.cursor()
    cursor.execute("SELECT version();")
    version = cursor.fetchone()
    print(f"PostgreSQL version: {version[0]}")

    conn.close()
    print("Connection closed.")

except Exception as e:
    print(f"\nConnection failed: {e}")