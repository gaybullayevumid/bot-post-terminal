import psycopg2
from data.config import DB_CONFIG

def get_db_connection():
    return psycopg2.connect(
        user=DB_CONFIG["user"],
        password=["password"],
        database=DB_CONFIG["database"],
        host=DB_CONFIG["host"]
    )
