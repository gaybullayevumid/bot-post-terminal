import logging
import psycopg2
import pandas as pd
from data.config import DB_CONFIG
# from sqlalchemy import create_engine



logging.basicConfig(level=logging.INFO)

# Ma'lumotlarni Excelga saqlash funksiyasi
def export_to_excel(month_name):
    try:
        # Oy nomlarini inglizchaga tarjima qilish
        month_mapping = {
            "Январь": 1, "Февраль": 2, "Март": 3,
            "Апрель": 4, "Май": 5, "Июнь": 6,
            "Июль": 7, "Август": 8, "Сентябрь": 9,
            "Октябрь": 10, "Ноябрь": 11, "Декабрь": 12
        }

        # Foydalanuvchidan kelgan oy nomini tarjima qilish
        month_number = month_mapping.get(month_name)
        if not month_number:
            raise ValueError(f"Noto'g'ri oy nomi: {month_name}")

        # PostgreSQL bilan ulanish
        conn = psycopg2.connect(**DB_CONFIG)

        # SQL so'rovni shakllantirish
        query = f"""
        SELECT * FROM arrearage 
        WHERE EXTRACT(MONTH FROM created_at) = {month_number}
          AND EXTRACT(YEAR FROM created_at) = 2025; -- Faqat 2025-yilni tekshirish
        """
        df = pd.read_sql_query(query, conn)

        # Excel faylga yozish
        file_path = f"{month_name}.xlsx"
        df.to_excel(file_path, index=False)

        # Ulanishni yopish
        conn.close()
        return file_path

    except Exception as e:
        logging.error(f"Xatolik yuz berdi: {e}")
        return None