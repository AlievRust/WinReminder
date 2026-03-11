"""Менеджер базы данных SQLite3 для приложения Reminder."""

import sqlite3
import threading
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from core.reminder import Reminder, Status


class DatabaseManager:
    """Менеджер для работы с SQLite базой данных."""

    def __init__(self, db_path: str = "data/reminders.db"):
        """
        Инициализация менеджера базы данных.

        Args:
            db_path: Путь к файлу базы данных
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._local = threading.local()
        self._init_database()

    def _get_connection(self) -> sqlite3.Connection:
        """
        Получить соединение с базой данных для текущего потока.

        Returns:
            Объект соединения SQLite
        """
        if not hasattr(self._local, "connection"):
            self._local.connection = sqlite3.connect(
                self.db_path,
                check_same_thread=False,
                detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES
            )
            self._local.connection.row_factory = sqlite3.Row
        return self._local.connection

    def _init_database(self):
        """Инициализация схемы базы данных."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS reminders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT,
                due_date TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending',
                repeat_interval TEXT,
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            )
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_due_date 
            ON reminders(due_date)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_status 
            ON reminders(status)
        """)

        conn.commit()

    def add_reminder(self, reminder: Reminder) -> int:
        """
        Добавить новое напоминание в базу данных.

        Args:
            reminder: Объект напоминания для добавления

        Returns:
            ID созданного напоминания
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO reminders (title, description, due_date, status, repeat_interval, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            reminder.title,
            reminder.description,
            reminder.due_date.isoformat(),
            reminder.status.value,
            reminder.repeat_interval,
            reminder.created_at.isoformat()
        ))

        conn.commit()
        return cursor.lastrowid

    def get_all_reminders(self) -> List[Reminder]:
        """
        Получить все напоминания из базы данных.

        Returns:
            Список всех напоминаний
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM reminders ORDER BY due_date ASC")
        rows = cursor.fetchall()
        return [self._row_to_reminder(row) for row in rows]

    def get_reminders_by_status(self, status: Status) -> List[Reminder]:
        """
        Получить напоминания с указанным статусом.

        Args:
            status: Статус для фильтрации

        Returns:
            Список напоминаний с указанным статусом
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT * FROM reminders WHERE status = ? ORDER BY due_date ASC",
            (status.value,)
        )
        rows = cursor.fetchall()
        return [self._row_to_reminder(row) for row in rows]

    def get_reminder_by_id(self, reminder_id: int) -> Optional[Reminder]:
        """
        Получить напоминание по ID.

        Args:
            reminder_id: ID напоминания

        Returns:
            Объект Reminder или None, если не найден
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM reminders WHERE id = ?", (reminder_id,))
        row = cursor.fetchone()
        return self._row_to_reminder(row) if row else None

    def update_status(self, reminder_id: int, status: Status) -> bool:
        """
        Обновить статус напоминания.

        Args:
            reminder_id: ID напоминания
            status: Новый статус

        Returns:
            True, если обновление успешно, иначе False
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute(
            "UPDATE reminders SET status = ? WHERE id = ?",
            (status.value, reminder_id)
        )
        conn.commit()
        return cursor.rowcount > 0

    def delete_reminder(self, reminder_id: int) -> bool:
        """
        Удалить напоминание из базы данных.

        Args:
            reminder_id: ID напоминания

        Returns:
            True, если удаление успешно, иначе False
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("DELETE FROM reminders WHERE id = ?", (reminder_id,))
        conn.commit()
        return cursor.rowcount > 0

    def get_pending_reminders(self, before: datetime) -> List[Reminder]:
        """
        Получить все ожидающие напоминания до указанного времени.

        Args:
            before: Момент времени для фильтрации

        Returns:
            Список напоминаний, которые должны сработать
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM reminders 
            WHERE status = 'pending' AND due_date <= ?
            ORDER BY due_date ASC
        """, (before.isoformat(),))
        rows = cursor.fetchall()
        return [self._row_to_reminder(row) for row in rows]

    def update_overdue_reminders(self) -> int:
        """
        Обновить статус просроченных напоминаний.

        Returns:
            Количество обновленных записей
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        now = datetime.now().isoformat()
        cursor.execute("""
            UPDATE reminders 
            SET status = 'overdue'
            WHERE status = 'pending' AND due_date < ?
        """, (now,))
        conn.commit()
        return cursor.rowcount

    def _row_to_reminder(self, row: sqlite3.Row) -> Reminder:
        """
        Преобразовать строку базы данных в объект Reminder.

        Args:
            row: Строка из SQLite

        Returns:
            Объект Reminder
        """
        return Reminder(
            id=row["id"],
            title=row["title"],
            description=row["description"],
            due_date=datetime.fromisoformat(row["due_date"]),
            status=Status(row["status"]),
            repeat_interval=row["repeat_interval"],
            created_at=datetime.fromisoformat(row["created_at"])
        )

    def close(self):
        """Закрыть соединение с базой данных."""
        if hasattr(self._local, "connection"):
            self._local.connection.close()
            del self._local.connection

    def __del__(self):
        """Деструктор для закрытия соединения."""
        self.close()