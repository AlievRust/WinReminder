"""Тесты для ReminderService."""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock

from core.service import ReminderService
from core.reminder import Reminder, Status
from core.scheduler import Scheduler
from core.database import DatabaseManager
from services.notification import NotificationService


class TestReminderService:
    """Тесты для класса ReminderService."""

    @pytest.fixture
    def mock_db(self):
        """Фикстура для мок-объекта базы данных."""
        return Mock(spec=DatabaseManager)

    @pytest.fixture
    def mock_notification_service(self):
        """Фикстура для мок-объекта сервиса уведомлений."""
        return Mock(spec=NotificationService)

    @pytest.fixture
    def service(self, mock_db, mock_notification_service):
        """Фикстура для создания сервиса с мок-объектами."""
        with patch.object(ReminderService, '__init__', lambda self, db_path=None, notification_service=None, check_interval=10: None):
            svc = ReminderService()
            svc.database = mock_db
            svc.notification_service = mock_notification_service
            svc.scheduler = Mock(spec=Scheduler)
            svc.scheduler.callback = None
            return svc

    def test_service_initialization(self):
        """Тест инициализации сервиса."""
        with patch('core.service.DatabaseManager') as mock_db_class, \
             patch('core.service.NotificationService') as mock_notif_class, \
             patch('core.service.Scheduler') as mock_scheduler_class:
            
            mock_db_instance = Mock()
            mock_db_class.return_value = mock_db_instance
            
            mock_notif_instance = Mock()
            mock_notif_class.return_value = mock_notif_instance
            
            mock_scheduler_instance = Mock()
            mock_scheduler_class.return_value = mock_scheduler_instance
            
            service = ReminderService(
                db_path="test.db",
                check_interval=15
            )
            
            # Проверяем, что все компоненты созданы
            assert service.database == mock_db_instance
            assert service.notification_service == mock_notif_instance
            assert service.scheduler == mock_scheduler_instance
            
            # Проверяем параметры планировщика
            mock_scheduler_class.assert_called_once()
            call_kwargs = mock_scheduler_class.call_args[1]
            assert call_kwargs['database'] == mock_db_instance
            assert call_kwargs['notification_service'] == mock_notif_instance
            assert call_kwargs['check_interval'] == 15

    def test_start(self, service):
        """Тест запуска сервиса."""
        service.start()
        service.scheduler.start.assert_called_once()

    def test_stop(self, service):
        """Тест остановки сервиса."""
        service.stop()
        service.scheduler.stop.assert_called_once()

    def test_set_refresh_callback(self, service):
        """Тест установки callback для обновления GUI."""
        callback = Mock()
        service.set_refresh_callback(callback)
        
        assert service._refresh_callback == callback
        assert service.scheduler.callback == callback

    def test_add_reminder(self, service):
        """Тест добавления напоминания."""
        reminder = Reminder(
            title="Тест",
            description="Описание",
            due_date=datetime.now()
        )
        service.database.add_reminder.return_value = 1
        
        result = service.add_reminder(reminder)
        
        assert result == 1
        service.database.add_reminder.assert_called_once_with(reminder)

    def test_get_all_reminders(self, service):
        """Тест получения всех напоминаний."""
        reminders = [Reminder(title="Тест1"), Reminder(title="Тест2")]
        service.database.get_all_reminders.return_value = reminders
        
        result = service.get_all_reminders()
        
        # Должен сначала обновить просроченные
        service.database.update_overdue_reminders.assert_called_once()
        service.database.get_all_reminders.assert_called_once()
        assert result == reminders

    def test_get_reminders_by_status(self, service):
        """Тест получения напоминаний по статусу."""
        reminders = [Reminder(title="Тест", status=Status.PENDING)]
        service.database.get_reminders_by_status.return_value = reminders
        
        result = service.get_reminders_by_status(Status.PENDING)
        
        # Должен сначала обновить просроченные
        service.database.update_overdue_reminders.assert_called_once()
        service.database.get_reminders_by_status.assert_called_once_with(Status.PENDING)
        assert result == reminders

    def test_get_reminder_by_id(self, service):
        """Тест получения напоминания по ID."""
        reminder = Reminder(title="Тест")
        service.database.get_reminder_by_id.return_value = reminder
        
        result = service.get_reminder_by_id(1)
        
        service.database.get_reminder_by_id.assert_called_once_with(1)
        assert result == reminder

    def test_update_status(self, service):
        """Тест обновления статуса."""
        service.database.update_status.return_value = True
        
        result = service.update_status(1, Status.DONE)
        
        assert result is True
        service.database.update_status.assert_called_once_with(1, Status.DONE)

    def test_delete_reminder(self, service):
        """Тест удаления напоминания."""
        service.database.delete_reminder.return_value = True
        
        result = service.delete_reminder(1)
        
        assert result is True
        service.database.delete_reminder.assert_called_once_with(1)

    def test_test_notification(self, service):
        """Тест тестового уведомления."""
        service.notification_service.test_notification.return_value = True
        
        result = service.test_notification()
        
        assert result is True
        service.notification_service.test_notification.assert_called_once()

    def test_trigger_check(self, service):
        """Тест принудительной проверки напоминаний."""
        reminders = [Reminder(title="Тест")]
        service.scheduler.check_and_notify.return_value = reminders
        
        result = service.trigger_check()
        
        assert result == reminders
        service.scheduler.check_and_notify.assert_called_once()

    def test_trigger_refresh_with_callback(self, service):
        """Тест вызова callback обновления."""
        callback = Mock()
        service._refresh_callback = callback
        
        service._trigger_refresh()
        
        callback.assert_called_once()

    def test_trigger_refresh_without_callback(self, service):
        """Тест вызова callback без установленного callback."""
        service._refresh_callback = None
        
        # Не должно вызывать исключения
        service._trigger_refresh()

    def test_refresh_callback_exception_handling(self, service):
        """Тест обработки исключений в callback."""
        callback = Mock()
        callback.side_effect = Exception("Test error")
        service._refresh_callback = callback
        
        # Не должно вызывать исключения
        service._trigger_refresh()


class TestReminderServiceIntegration:
    """Интеграционные тесты для ReminderService."""

    def test_full_integration(self, tmp_path):
        """Интеграционный тест полного цикла работы сервиса."""
        # Используем временную базу данных
        db_path = tmp_path / "test_reminders.db"
        
        service = ReminderService(db_path=str(db_path))
        
        # Запускаем сервис
        service.start()
        
        try:
            # Добавляем напоминание на будущее
            now = datetime.now()
            future_date = now + timedelta(hours=1)
            
            reminder = Reminder(
                title="Интеграционный тест",
                description="Тестовое описание",
                due_date=future_date,
                status=Status.PENDING
            )
            
            reminder_id = service.add_reminder(reminder)
            assert reminder_id > 0
            
            # Получаем напоминание
            fetched = service.get_reminder_by_id(reminder_id)
            assert fetched is not None
            assert fetched.title == "Интеграционный тест"
            
            # Получаем все напоминания
            all_reminders = service.get_all_reminders()
            assert len(all_reminders) == 1
            
            # Обновляем статус
            service.update_status(reminder_id, Status.DONE)
            
            updated = service.get_reminder_by_id(reminder_id)
            assert updated.status == Status.DONE
            
            # Удаляем напоминание
            service.delete_reminder(reminder_id)
            
            deleted = service.get_reminder_by_id(reminder_id)
            assert deleted is None
            
        finally:
            # Останавливаем сервис
            service.stop()

    def test_callback_invocation_on_reminder_add(self, tmp_path):
        """Тест вызова callback при добавлении напоминания."""
        db_path = tmp_path / "test_reminders.db"
        service = ReminderService(db_path=str(db_path))
        
        callback_invoked = False
        
        def refresh_callback():
            nonlocal callback_invoked
            callback_invoked = True
        
        service.set_refresh_callback(refresh_callback)
        
        # Добавляем напоминание
        reminder = Reminder(
            title="Тест callback",
            due_date=datetime.now() + timedelta(hours=1)
        )
        service.add_reminder(reminder)
        
        assert callback_invoked is True

    def test_callback_invocation_on_status_update(self, tmp_path):
        """Тест вызова callback при обновлении статуса."""
        db_path = tmp_path / "test_reminders.db"
        service = ReminderService(db_path=str(db_path))
        
        callback_invoked = False
        
        def refresh_callback():
            nonlocal callback_invoked
            callback_invoked = True
        
        service.set_refresh_callback(refresh_callback)
        
        # Добавляем напоминание
        reminder = Reminder(
            title="Тест callback",
            due_date=datetime.now() + timedelta(hours=1)
        )
        reminder_id = service.add_reminder(reminder)
        
        # Сбрасываем флаг
        callback_invoked = False
        
        # Обновляем статус
        service.update_status(reminder_id, Status.DONE)
        
        assert callback_invoked is True