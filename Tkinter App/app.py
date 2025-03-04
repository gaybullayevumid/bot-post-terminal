import mysql.connector
import psycopg2
from tkinter import Tk, Button, Label, messagebox

# MySQL va PostgreSQL ulanish parametrlari
mysql_config = {
    'user': 'root',
    'password': '8505',
    'host': 'localhost',
    'database': 'easytrade_db'
}

postgres_config = {
    'dbname': 'avtolider',
    'user': 'postgres',
    'password': '8505',
    'host': 'localhost'
}


def get_mysql_tables():
    """MySQL dan barcha jadvallarni olish"""
    conn = mysql.connector.connect(**mysql_config)
    cursor = conn.cursor()
    cursor.execute("SHOW TABLES")
    tables = [table[0] for table in cursor.fetchall()]
    cursor.close()
    conn.close()
    return tables


def get_mysql_table_schema(table_name):
    """MySQL jadvalining tuzilishini olish"""
    conn = mysql.connector.connect(**mysql_config)
    cursor = conn.cursor(dictionary=True)

    cursor.execute(
        f"SELECT COLUMN_NAME, DATA_TYPE FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = '{table_name}' AND TABLE_SCHEMA = '{mysql_config['database']}'")
    columns = cursor.fetchall()

    cursor.close()
    conn.close()
    return columns


def create_postgres_table(table_name, columns):
    """Agar PostgreSQL da jadval bo'lmasa, uni yaratish"""
    postgres_conn = psycopg2.connect(**postgres_config)
    postgres_cursor = postgres_conn.cursor()

    # MySQL -> PostgreSQL ma'lumotlar turini moslashtirish
    mysql_to_postgres_types = {
        'int': 'INTEGER',
        'varchar': 'TEXT',
        'text': 'TEXT',
        'datetime': 'TIMESTAMP',
        'date': 'DATE',
        'float': 'REAL',
        'double': 'DOUBLE PRECISION',
        'tinyint': 'SMALLINT',
        'bigint': 'BIGINT'
    }

    column_definitions = []
    for col in columns:
        pg_type = mysql_to_postgres_types.get(col["DATA_TYPE"], "TEXT")
        column_definitions.append(f'"{col["COLUMN_NAME"]}" {pg_type}')

    create_table_query = f'CREATE TABLE IF NOT EXISTS "{table_name}" ({", ".join(column_definitions)})'

    postgres_cursor.execute(create_table_query)
    postgres_conn.commit()

    postgres_cursor.close()
    postgres_conn.close()


def copy_table_to_postgres(table_name):
    """MySQL jadvalidan ma'lumotlarni PostgreSQL ga ko'chirish"""
    mysql_conn = mysql.connector.connect(**mysql_config)
    mysql_cursor = mysql_conn.cursor(dictionary=True)
    mysql_cursor.execute(f"SELECT * FROM {table_name}")
    rows = mysql_cursor.fetchall()

    columns = get_mysql_table_schema(table_name)
    create_postgres_table(table_name, columns)

    postgres_conn = psycopg2.connect(**postgres_config)
    postgres_cursor = postgres_conn.cursor()

    # Ma'lumotlarni ko'chirish
    for row in rows:
        columns = ', '.join([f'"{key}"' for key in row.keys()])
        values = ', '.join(['%s'] * len(row))
        insert_query = f'INSERT INTO "{table_name}" ({columns}) VALUES ({values})'
        postgres_cursor.execute(insert_query, list(row.values()))

    postgres_conn.commit()
    mysql_cursor.close()
    mysql_conn.close()
    postgres_cursor.close()
    postgres_conn.close()


def sync_databases():
    """Barcha jadvallarni MySQL dan PostgreSQL ga ko'chirish"""
    tables = get_mysql_tables()
    for table in tables:
        copy_table_to_postgres(table)
    messagebox.showinfo("Muvaffaqiyat", "Ma'lumotlar muvaffaqiyatli ko'chirildi!")


# Tkinter ilovasi
root = Tk()
root.title("MySQL to PostgreSQL Sync")

label = Label(root, text="MySQL dan PostgreSQL ga ma'lumotlarni ko'chirish")
label.pack(pady=10)

sync_button = Button(root, text="Sinxronizatsiya", command=sync_databases)
sync_button.pack(pady=20)

root.mainloop()
