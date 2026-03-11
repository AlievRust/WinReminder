"""Сервисный слой для работы с напоминаниями."""

from typing import List, Optional, Callable

from core.database import DatabaseManager
from core.reminder import Reminder, Status
from core.scheduler import Scheduler
from services.notification import NotificationService


class ReminderService:
    """
    Сервисный слой для управления напоминаниями.
    
    Объединяет DatabaseManager и Scheduler, предоставляя единый интерфейс
    для работы с напоминаниями, включая фоновую проверку и отправку уведомлений.
    """

    def __init__(
        self,
        db_path: str = "data/reminders.db",
        notification_service: Optional[NotificationService] = None,
        check_interval: int = 10
    ):
        """
        Инициализация сервиса напоминаний.

        Args:
            db_path: Путь к файлу базы данных
            notification_service: Сервис уведомлений (опционально)
            check_interval: Интервал проверки напоминаний в секундах
        """
        self.database = DatabaseManager(db_path)
        self.notification_service = notification_service or NotificationService()
        
        # Создаём планировщик без callback (callback можно добавить позже)
        self.scheduler = Scheduler(
            database=self.database,
            notification_service=self.notification_service,
            check_interval=check_interval
        )
        
        # Callback для обновления GUI
        self._refresh_callback: Optional[Callable] = None

    def start(self):
        """Запустить сервис напоминаний (включая планировщик)."""
        self.scheduler.start()

    def stop(self):
        """Остановить сервис напоминаний (включая планировщик)."""
        self.scheduler.stop()

    def set_refresh_callback(self, callback: Callable):
        """
        Установить callback-функцию для обновления GUI.

        Args:
            callback: Функция, которая будет вызываться при изменениях
        """
        self._refresh_callback = callback
        self.scheduler.callback = callback

    # ========== Операции CRUD ==========

    def add_reminder(self, reminder: Reminder) -> int:
        """
        Добавить новое напоминание.

        Args:
            reminder: Объект напоминания для добавления

        Returns:
            ID созданного напоминания
        """
        reminder_id = self.database.add_reminder(reminder)
        self._trigger_refresh()
        return reminder_id

    def get_all_reminders(self) -> List[Reminder]:
        """
        Получить все напоминания.

        Returns:
            Список всех напоминаний
        """
        self.database.update_overdue_reminders()
        return self.database.get_all_reminders()

    def get_reminders_by_status(self, status: Status) -> List[Reminder]:
        """
        Получить напоминания с указанным статусом.

        Args:
            status: Статус для фильтрации

        Returns:
            Список напоминаний с указанным статусом
        """
        self.database.update_overdue_reminders()
        return self.database.get_reminders_by_status(status)

    def get_reminder_by_id(self, reminder_id: int) -> Optional[Reminder]:
        """
        Получить напоминание по ID.

        Args:
            reminder_id: ID напоминания

        Returns:
            Объект Reminder или None, если не найден
        """
        return self.database.get_reminder_by_id(reminder_id)

    def update_status(self, reminder_id: int, status: Status) -> bool:
        """
        Обновить статус напоминания.

        Args:
            reminder_id: ID напоминания
            status: Новый статус

        Returns:
            True, если обновление успешно, иначе False
        """
        result = self.database.update_status(reminder_id, status)
        self._trigger_refresh()
        return result

    def delete_reminder(self, reminder_id: int) -> bool:
        """
        Удалить напоминание.

        Args:
            reminder_id: ID напоминания

        Returns:
            True, если удаление успешно, иначе False
        """
        result = self.database.delete_reminder(reminder_id)
        self._trigger_refresh()
        return result

    # ========== Управление планировщиком ==========

    def test_notification(self) -> bool:
        """
        Показать тестовое уведомление.

        Returns:
            True, если уведомление отправлено успешно
        """
        return self.notification_service.test_notification()

    def trigger_check(self) -> List[Reminder]:
        """
        Принудительно проверить и отправить напоминания.

        Returns:
            Список обработанных напоминаний
        """
        return self.scheduler.check_and_notify()

    # ========== Вспомогательные методы ==========

    def _trigger_refresh(self):
        """Вызвать callback для обновления GUI, если он установлен."""
        callback = getattr(self, '_refresh_callback', None)
        if callback:
            try:
                callback()
            except Exception as e:
                print(f"Ошибка при вызове callback обновления: {e}")

    def __del__(self):
        """Деструктор для корректной остановки сервиса."""
        self.stop()