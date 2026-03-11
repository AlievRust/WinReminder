"""Сервис системных уведомлений на базе plyer."""

from plyer import notification
from typing import Optional


class NotificationService:
    """Класс для отправки системных уведомлений Windows."""

    def __init__(
        self,
        app_name: str = "Reminder",
        app_icon: Optional[str] = None
    ):
        """
        Инициализация сервиса уведомлений.

        Args:
            app_name: Название приложения для отображения в уведомлении
            app_icon: Путь к иконке приложения (опционально)
        """
        self.app_name = app_name
        self.app_icon = app_icon

    def show_notification(
        self,
        title: str,
        message: str,
        timeout: int = 10
    ) -> bool:
        """
        Показать системное уведомление.

        Args:
            title: Заголовок уведомления
            message: Текст сообщения
            timeout: Время отображения в секундах

        Returns:
            True, если уведомление отправлено успешно, иначе False
        """
        try:
            notification.notify(
                title=title,
                message=message,
                app_name=self.app_name,
                app_icon=self.app_icon,
                timeout=timeout
            )
            return True
        except Exception as e:
            print(f"Ошибка при отправке уведомления: {e}")
            return False

    def test_notification(self) -> bool:
        """
        Показать тестовое уведомление.

        Returns:
            True, если уведомление отправлено успешно
        """
        return self.show_notification(
            title="Тестовое уведомление",
            message="Уведомления работают корректно!"
        )


# Глобальный экземпляр для использования в приложении
_notification_service: Optional[NotificationService] = None


def get_notification_service() -> NotificationService:
    """
    Получить (или создать) глобальный экземпляр сервиса уведомлений.

    Returns:
        Экземпляр NotificationService
    """
    global _notification_service
    if _notification_service is None:
        _notification_service = NotificationService()
    return _notification_service
