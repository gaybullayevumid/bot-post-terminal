import psycopg2
from data.config import DB_CONFIG

def get_db_connection():
    return psycopg2.connect(
        user=DB_CONFIG["user"],
        password=["password"],
        database=DB_CONFIG["database"],
        host=DB_CONFIG["host"]
    )

def owner_phone(phone_number):
    global cursor, conn
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
                INSERT INTO owner_phone(phone)
                VALUES %s
                ON CONFLICT (phone) DO NOTHING
            """, (phone_number))

        conn.commit()
    except Exception as error:
        print(error)

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()



def add_user(telegram_id, username):
    connect = get_db_connection()
    cursor = connect.cursor()

    try:
        cursor.execute(
            """
                INSERT INTO users(telegram_id, username)
                VALUES (%s, %s)
                ON CONFLICT (telegram_id) DO NOTHING
            """,
            (telegram_id, username)
        )

        connect.commit()

    except Exception as error:
        print(f"Bazada xatolik {error}")

    finally:
        cursor.close()
        connect.close()