"""Планировщик для проверки и отправки напоминаний в фоновом режиме."""

import threading
import time
from datetime import datetime, timedelta
from typing import Callable, Optional, List

from core.reminder import Reminder, Status
from core.database import DatabaseManager
from services.notification import NotificationService


class Scheduler:
    """Фоновый планировщик для проверки и отправки уведомлений."""

    def __init__(
        self,
        database: DatabaseManager,
        notification_service: NotificationService,
        check_interval: int = 10,
        callback: Optional[Callable] = None
    ):
        """
        Инициализация планировщика.

        Args:
            database: Менеджер базы данных для работы с напоминаниями
            notification_service: Сервис для отправки уведомлений
            check_interval: Интервал проверки в секундах (по умолчанию 10)
            callback: Функция для вызова при обновлении напоминаний
                     (например, для обновления GUI)
        """
        self.database = database
        self.notification_service = notification_service
        self.check_interval = check_interval
        self.callback = callback
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()

    def start(self):
        """Запустить фоновый поток планировщика."""
        if self._running:
            print("Планировщик уже запущен")
            return

        self._running = True
        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._run,
            name="ReminderScheduler",
            daemon=True
        )
        self._thread.start()
        print(f"Планировщик запущен (интервал: {self.check_interval} сек)")

    def stop(self):
        """Остановить фоновый поток планировщика."""
        if not self._running:
            print("Планировщик не запущен")
            return

        self._running = False
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=5)
            if self._thread.is_alive():
                print("Предупреждение: поток планировщика не остановился вовремя")
        print("Планировщик остановлен")

    def _run(self):
        """Основной цикл планировщика в фоновом потоке."""
        while not self._stop_event.is_set():
            try:
                self.check_and_notify()
            except Exception as e:
                print(f"Ошибка при проверке напоминаний: {e}")

            # Ожидание с возможностью досрочной остановки
            self._stop_event.wait(self.check_interval)

    def check_and_notify(self) -> List[Reminder]:
        """
        Проверить и отправить уведомления для просроченных напоминаний.

        Returns:
            Список обработанных напоминаний
        """
        now = datetime.now()
        pending_reminders = self.database.get_pending_reminders(now)
        processed = []

        for reminder in pending_reminders:
            try:
                # Отправляем уведомление
                self._send_reminder_notification(reminder)

                # Обрабатываем напоминание
                if reminder.is_recurring():
                    # Создаём следующее повторение
                    next_reminder = self._create_next_reminder(reminder)
                    self.database.add_reminder(next_reminder)
                    # Текущее помечаем как выполненное
                    self.database.update_status(reminder.id, Status.DONE)
                else:
                    # Однократное напоминание - помечаем как выполненное
                    self.database.update_status(reminder.id, Status.DONE)

                processed.append(reminder)
            except Exception as e:
                print(f"Ошибка при обработке напоминания {reminder.id}: {e}")

        # Обновляем статус просроченных напоминаний
        self.database.update_overdue_reminders()

        # Вызываем callback, если есть (например, для обновления GUI)
        if processed and self.callback:
            try:
                self.callback()
            except Exception as e:
                print(f"Ошибка при вызове callback: {e}")

        return processed

    def _send_reminder_notification(self, reminder: Reminder):
        """
        Отправить уведомление для напоминания.

        Args:
            reminder: Напоминание для отправки уведомления
        """
        title = reminder.title or "Напоминание"
        message = reminder.description or "Наступило время напоминания"
        
        # Добавляем информацию о повторении, если есть
        if reminder.is_recurring():
            message += f" (Повторение: {reminder.repeat_interval})"
        
        self.notification_service.show_notification(
            title=title,
            message=message
        )

    def _create_next_reminder(self, reminder: Reminder) -> Reminder:
        """
        Создать следующее повторение напоминания.

        Args:
            reminder: Исходное напоминание

        Returns:
            Новое напоминание с обновлённой датой
        """
        interval = reminder.repeat_interval
        due_date = reminder.due_date

        # Вычисляем новую дату в зависимости от интервала
        if interval == "hour":
            due_date = due_date + timedelta(hours=1)
        elif interval == "day":
            due_date = due_date + timedelta(days=1)
        elif interval == "week":
            due_date = due_date + timedelta(weeks=1)
        elif interval == "month":
            # Используем dateutil для добавления месяцев (корректно обрабатывает переходы)
            from dateutil.relativedelta import relativedelta
            due_date = due_date + relativedelta(months=1)
        else:
            raise ValueError(f"Неизвестный интервал повтора: {interval}")

        # Создаём новое напоминание
        return Reminder(
            title=reminder.title,
            description=reminder.description,
            due_date=due_date,
            status=Status.PENDING,
            repeat_interval=reminder.repeat_interval
        )

    def is_running(self) -> bool:
        """
        Проверить, запущен ли планировщик.

        Returns:
            True, если планировщик запущен
        """
        return self._running

    def __del__(self):
        """Деструктор для корректной остановки."""
        self.stop()
