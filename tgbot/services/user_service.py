from typing import List, Dict, Any, Optional
from loguru import logger
from tgbot.services.base_service import BaseService
from tgbot.models.models import TGUser


class UserService(BaseService):
    """Сервис для пользовательских операций"""
    
    async def get_user_by_telegram_id(self, telegram_id: int) -> Optional[TGUser]:
        """
        Получить пользователя по Telegram ID.
        
        SQL:
        SELECT *
        FROM telegram_users
        WHERE telegram_id = :telegram_id;
        """
        return await self.safe_execute(
            "get_user_by_telegram_id",
            TGUser.get_user,
            self.db,
            telegram_id
        )
    
    async def update_user_phone(self, telegram_id: int, phone: str) -> Optional[TGUser]:
        """
        Обновить номер телефона пользователя по Telegram ID.
        
        SQL:
        UPDATE telegram_users
        SET phone = :phone
        WHERE telegram_id = :telegram_id;
        """
        return await self.safe_execute(
            "update_user_phone",
            TGUser.update_user,
            self.db,
            telegram_id,
            phone=phone
        )
    
    async def get_user_invoice(self, phone: str, month: str) -> List[Dict[str, Any]]:
        """
        Получить накладную пользователя по номеру телефона и месяцу.
        
        SQL:
        SELECT
            o.obj_name         AS "Магазин/Склад",
            g.gd_code          AS "Код",
            g.gd_name          AS "Номенклатура",
            s.sls_datetime     AS "Дата/Время",
            'Продажа'          AS "Тип",
            op.opr_quantity    AS "Количество",
            a.oap_price1       AS "Цена",
            (op.opr_quantity * a.oap_price1) AS "Сумма",
            dss.sords_name     AS "Статус оплаты"
        FROM doc_sales s
            JOIN operations op ON op.opr_document = s.sls_id AND op.opr_type = 2
            JOIN operations_additional_prop a ON a.oap_operation = op.opr_id
            JOIN dir_goods g ON g.gd_id = op.opr_good
            JOIN dir_objects o ON o.obj_id = s.sls_object
            JOIN dir_customers c ON c.cstm_id = s.sls_customer
            JOIN dir_sales_status dss ON dss.sords_id = s.sls_status
        WHERE
            s.sls_datetime BETWEEN '2015-01-01' AND '2044-06-15'
            AND s.sls_performed = 1
            AND s.sls_deleted = 0
            AND :phone IN (c.cstm_phone, c.cstm_phone2, c.cstm_phone3, c.cstm_phone4)
            AND dss.sords_name != 'Завершен'
            AND EXTRACT(MONTH FROM s.sls_datetime) = :month
        ORDER BY s.sls_datetime DESC;
        """
        return await TGUser.get_user_invoice(self.db, phone, month)
    
    async def get_user_reconciliation(self, phone: str, year: int, month: int) -> List[Dict[str, Any]]:
        """
        Получить данные акта сверки пользователя по номеру телефона, году и месяцу.
        
        SQL:
        SELECT
            s.sls_datetime AS "Дата",
            'Реализация №' || s.sls_id AS "Документ",
            SUM(op.opr_quantity * a.oap_price1) AS "Сумма",
            SUM(CASE WHEN dco.cop_type IN (1,4) THEN dco.cop_value ELSE 0 END) AS "Оплачено",
            (SUM(op.opr_quantity * a.oap_price1) - SUM(CASE WHEN dco.cop_type IN (1,4) THEN dco.cop_value ELSE 0 END)) AS "Долг",
            s.sls_note AS "Примечание"
        FROM doc_sales s
            LEFT JOIN operations op ON op.opr_document = s.sls_id AND op.opr_type = 2
            LEFT JOIN operations_additional_prop a ON a.oap_operation = op.opr_id
            LEFT JOIN doc_cash_operations dco ON dco.cop_payment = s.sls_id
            JOIN dir_customers c ON s.sls_customer = c.cstm_id
        WHERE
            (c.cstm_phone = :phone OR c.cstm_phone2 = :phone OR c.cstm_phone3 = :phone OR c.cstm_phone4 = :phone)
            AND s.sls_performed = 1
            AND s.sls_deleted = 0
            AND EXTRACT(YEAR FROM s.sls_datetime) = :year
            AND EXTRACT(MONTH FROM s.sls_datetime) = :month
        GROUP BY s.sls_id, s.sls_datetime, s.sls_note
        ORDER BY s.sls_datetime DESC, s.sls_id DESC;
        """
        return await TGUser.get_customer_sales_summary(self.db, phone, year, month)
    
    async def get_customer_name(self, phone: str) -> str:
        """
        Получить название покупателя по номеру телефона.
        
        SQL:
        SELECT
            c.cstm_name AS name
        FROM dir_customers c
        WHERE
            c.cstm_phone = :phone
            OR c.cstm_phone2 = :phone
            OR c.cstm_phone3 = :phone
            OR c.cstm_phone4 = :phone
        LIMIT 1;
        """
        return await TGUser.get_customer_name_by_phone(self.db, phone)
    
    def format_reconciliation_summary(self, summary: List[Dict[str, Any]], phone: str, year: int, month: int) -> str:
        """
        Форматировать сводку акта сверки для пользователя.
        
        summary: список словарей с ключами 'Сумма', 'Долг', 'Документ', ...
        Возвращает текстовое сообщение для Telegram.
        """
        if not summary:
            return f"❌ За {month}/{year} данные для акта сверки не найдены"
        
        total_debt = sum(float(row.get('Долг', 0) or 0) for row in summary)
        total_sum = sum(float(row.get('Сумма', 0) or 0) for row in summary)
        
        return (
            f"📄 <b>Акт сверки за {month}/{year}</b>\n"
            f"📱 Телефон: <b>{phone}</b>\n\n"
            f"📊 Найдено: {len(summary)} документов\n"
            f"💵 Общая сумма за период: <b>{self.format_currency(total_sum)}</b>\n"
            f"💰 Итоговый долг: <b>{self.format_currency(total_debt)}</b>\n\n"
            "📄 Генерируем Excel файл..."
        )
    
    def get_reconciliation_excel_params(self, customer_name: str, year: int, month: int, total_debt: float) -> Dict[str, Any]:
        """
        Получить параметры для Excel-файла акта сверки.
        
        Возвращает словарь с параметрами для генерации Excel:
        - company1: название компании
        - company2: имя клиента
        - period_start: дата начала периода
        - period_end: дата конца периода
        - saldo_start: начальный баланс
        - saldo_end: конечный баланс
        """
        return {
            "company1": "AVTOLIDER",
            "company2": customer_name,
            "period_start": f"01.{month}.{year}",
            "period_end": f"31.{month}.{year}",
            "saldo_start": 0.0,
            "saldo_end": total_debt
        }
    
    async def get_user_reconciliation_act_rows(self, phone: str, year: int, month: int):
        """
        Получить строки для акта сверки пользователя в формате для Excel.
        
        Использует TGUser.get_filtered_sales_summary, который выполняет:
        
        SQL:
        SELECT
            s.sls_datetime AS "Дата",
            'Реализация №' || s.sls_id AS "Документ",
            SUM(op.opr_quantity * a.oap_price1) AS "Сумма",
            SUM(CASE WHEN dco.cop_type IN (1,4) THEN dco.cop_value ELSE 0 END) AS "Оплачено",
            (SUM(op.opr_quantity * a.oap_price1) - SUM(CASE WHEN dco.cop_type IN (1,4) THEN dco.cop_value ELSE 0 END)) AS "Долг"
        FROM doc_sales s
            LEFT JOIN operations op ON op.opr_document = s.sls_id AND op.opr_type = 2
            LEFT JOIN operations_additional_prop a ON a.oap_operation = op.opr_id
            LEFT JOIN doc_cash_operations dco ON dco.cop_payment = s.sls_id
            [JOIN dir_customers c ON s.sls_customer = c.cstm_id]
        WHERE
            YEAR(s.sls_datetime) = :year
            AND MONTH(s.sls_datetime) = :month
            AND s.sls_performed = 1
            AND s.sls_deleted = 0
            [AND c.cstm_id = :customer_id]
            [AND (c.cstm_phone = :phone OR ...)]
        GROUP BY s.sls_id, s.sls_datetime
        ORDER BY s.sls_datetime DESC, s.sls_id DESC;
        
        Возвращает список словарей для Excel-таблицы.
        """
        try:
            rows = await TGUser.get_filtered_sales_summary(self.db, year, month, phone_number=phone)
            result = []
            for row in rows:
                # Определяем тип операции по примечанию или суммам
                note = row.get('Примечание', '') or ''
                doc = row.get('Документ', '')
                summa = float(row.get('Сумма', 0) or 0)
                paid = float(row.get('Оплачено', 0) or 0)
                debt = float(row.get('Долг', 0) or 0)
                # По умолчанию все 0
                r = {
                    'Дата': row.get('Дата'),
                    'Документ': note if note else doc,
                    'Дебет1': 0.0,
                    'Долг1': 0.0,
                    'Долг2': 0.0,
                    'Дебет2': 0.0,
                    'Кредит': 0.0,
                    'Кредит2': 0.0
                }
                # Логика распределения по колонкам (примерная)
                if 'отгрузка' in note.lower() or 'реализац' in doc.lower():
                    # Продажа/отгрузка
                    r['Дебет1'] = summa
                    r['Кредит'] = summa
                elif 'оплата' in note.lower():
                    # Оплата
                    r['Долг1'] = paid
                    r['Дебет2'] = paid
                elif 'возврат' in note.lower():
                    # Возврат
                    r['Долг2'] = paid
                else:
                    # Если не определили — просто сумма в дебет
                    r['Дебет1'] = summa
                result.append(r)
            logger.info(f"UserService.get_user_reconciliation_act_rows: phone={phone}, year={year}, month={month}, rows={len(result)}")
            return result
        except Exception as e:
            logger.error(f"UserService.get_user_reconciliation_act_rows error: {e}")
            raise 