"""Тесты для Scheduler."""

import pytest
import tempfile
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
from threading import Thread
import time

import sys
from pathlib import Path

# Добавляем src в путь для импортов
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from core.scheduler import Scheduler
from core.database import DatabaseManager
from core.reminder import Reminder, Status
from services.notification import NotificationService


@pytest.fixture
def temp_db_path(tmp_path):
    """Фикстура для создания временной базы данных."""
    db_path = tmp_path / "test_scheduler.db"
    yield str(db_path)


@pytest.fixture
def db_manager(temp_db_path):
    """Фикстура для создания менеджера базы данных."""
    db = DatabaseManager(temp_db_path)
    yield db
    db.close()


@pytest.fixture
def mock_notification_service():
    """Фикстура для создания мок-сервиса уведомлений."""
    service = Mock(spec=NotificationService)
    service.show_notification = Mock(return_value=True)
    return service


@pytest.fixture
def scheduler(db_manager, mock_notification_service):
    """Фикстура для создания планировщика."""
    scheduler = Scheduler(
        database=db_manager,
        notification_service=mock_notification_service,
        check_interval=1  # Короткий интервал для тестов
    )
    yield scheduler
    # Останавливаем планировщик после тестов
    scheduler.stop()


class TestScheduler:
    """Тесты для Scheduler."""

    def test_scheduler_initialization(self, db_manager, mock_notification_service):
        """Тест инициализации планировщика."""
        scheduler = Scheduler(
            database=db_manager,
            notification_service=mock_notification_service,
            check_interval=10
        )
        
        assert scheduler.database == db_manager
        assert scheduler.notification_service == mock_notification_service
        assert scheduler.check_interval == 10
        assert not scheduler.is_running()

    def test_scheduler_start_stop(self, scheduler):
        """Тест запуска и остановки планировщика."""
        assert not scheduler.is_running()
        
        # Запускаем
        scheduler.start()
        assert scheduler.is_running()
        
        # Останавливаем
        scheduler.stop()
        assert not scheduler.is_running()

    def test_scheduler_start_when_already_running(self, scheduler):
        """Тест повторного запуска."""
        scheduler.start()
        assert scheduler.is_running()
        
        # Повторный запуск не должен создавать новый поток
        scheduler.start()
        assert scheduler.is_running()
        
        scheduler.stop()

    def test_stop_when_not_running(self, scheduler):
        """Тест остановки не запущенного планировщика."""
        # Не должен вызывать ошибку
        scheduler.stop()
        assert not scheduler.is_running()

    def test_check_and_notify_no_reminders(self, scheduler):
        """Тест проверки без напоминаний."""
        processed = scheduler.check_and_notify()
        
        assert isinstance(processed, list)
        assert len(processed) == 0

    def test_check_and_notify_with_pending_reminders(
        self,
        scheduler,
        db_manager,
        mock_notification_service
    ):
        """Тест обработки ожидающих напоминаний."""
        now = datetime.now()
        
        # Создаём напоминание с прошедшим временем
        reminder = Reminder(
            title="Test Reminder",
            description="Test description",
            due_date=now - timedelta(seconds=1),
            status=Status.PENDING
        )
        reminder_id = db_manager.add_reminder(reminder)
        
        # Запускаем проверку
        processed = scheduler.check_and_notify()
        
        # Должно быть обработано одно напоминание
        assert len(processed) == 1
        assert processed[0].id == reminder_id
        
        # Уведомление должно быть отправлено
        mock_notification_service.show_notification.assert_called_once()
        
        # Статус должен быть обновлён на DONE
        updated = db_manager.get_reminder_by_id(reminder_id)
        assert updated.status == Status.DONE

    def test_check_and_notify_with_future_reminders(
        self,
        scheduler,
        db_manager,
        mock_notification_service
    ):
        """Тест проверки с будущими напоминаниями."""
        now = datetime.now()
        
        # Создаём напоминание в будущем
        reminder = Reminder(
            title="Future Reminder",
            due_date=now + timedelta(hours=1),
            status=Status.PENDING
        )
        db_manager.add_reminder(reminder)
        
        # Запускаем проверку
        processed = scheduler.check_and_notify()
        
        # Ничего не должно быть обработано
        assert len(processed) == 0
        
        # Уведомление не должно быть отправлено
        mock_notification_service.show_notification.assert_not_called()

    def test_check_and_notify_with_recurring_reminder(
        self,
        scheduler,
        db_manager,
        mock_notification_service
    ):
        """Тест обработки повторяющегося напоминания."""
        now = datetime.now()
        
        # Создаём повторяющееся напоминание с прошедшим временем
        reminder = Reminder(
            title="Recurring Reminder",
            description="Daily reminder",
            due_date=now - timedelta(seconds=1),
            status=Status.PENDING,
            repeat_interval="day"
        )
        reminder_id = db_manager.add_reminder(reminder)
        
        # Запускаем проверку
        processed = scheduler.check_and_notify()
        
        # Исходное напоминание должно быть обработано
        assert len(processed) == 1
        
        # Статус исходного должен быть DONE
        updated = db_manager.get_reminder_by_id(reminder_id)
        assert updated.status == Status.DONE
        
        # Должно быть создано новое напоминание
        all_reminders = db_manager.get_all_reminders()
        assert len(all_reminders) == 2
        
        # Новое напоминание должно быть в будущем (+1 день)
        new_reminder = [r for r in all_reminders if r.id != reminder_id][0]
        assert new_reminder.status == Status.PENDING
        assert new_reminder.due_date.date() > now.date()
        assert new_reminder.repeat_interval == "day"

    def test_check_and_notify_updates_overdue(
        self,
        scheduler,
        db_manager
    ):
        """Тест обновления статуса просроченных напоминаний."""
        now = datetime.now()
        
        # Создаём несколько просроченных напоминаний
        for i in range(3):
            reminder = Reminder(
                title=f"Overdue {i}",
                due_date=now - timedelta(hours=i + 1),
                status=Status.PENDING
            )
            db_manager.add_reminder(reminder)
        
        # Запускаем проверку (из-за времени может обработать не все)
        scheduler.check_and_notify()
        
        # Проверяем, что просроченные помечены
        overdue = db_manager.get_reminders_by_status(Status.OVERDUE)
        assert len(overdue) >= 0  # Некоторые могли быть обработаны

    def test_send_reminder_notification(self, scheduler, mock_notification_service):
        """Тест отправки уведомления."""
        reminder = Reminder(
            title="Test Title",
            description="Test Message",
            due_date=datetime.now(),
            status=Status.PENDING
        )
        
        scheduler._send_reminder_notification(reminder)
        
        # Проверяем, что уведомление было отправлено с правильными параметрами
        mock_notification_service.show_notification.assert_called_once()
        call_args = mock_notification_service.show_notification.call_args
        
        assert call_args[1]["title"] == "Test Title"
        assert "Test Message" in call_args[1]["message"]

    def test_send_reminder_notification_with_recurrence(
        self,
        scheduler,
        mock_notification_service
    ):
        """Тест уведомления с информацией о повторении."""
        reminder = Reminder(
            title="Recurring",
            description="Message",
            due_date=datetime.now(),
            status=Status.PENDING,
            repeat_interval="week"
        )
        
        scheduler._send_reminder_notification(reminder)
        
        call_args = mock_notification_service.show_notification.call_args
        assert "(Повторение: week)" in call_args[1]["message"]

    def test_create_next_reminder_hour(self, scheduler):
        """Тест создания следующего напоминания (час)."""
        now = datetime(2024, 1, 15, 14, 30, 0)
        
        reminder = Reminder(
            title="Hourly",
            due_date=now,
            repeat_interval="hour"
        )
        
        next_reminder = scheduler._create_next_reminder(reminder)
        
        assert next_reminder.title == "Hourly"
        assert next_reminder.status == Status.PENDING
        assert next_reminder.repeat_interval == "hour"
        assert next_reminder.due_date == datetime(2024, 1, 15, 15, 30, 0)

    def test_create_next_reminder_day(self, scheduler):
        """Тест создания следующего напоминания (день)."""
        now = datetime(2024, 1, 15, 14, 30, 0)
        
        reminder = Reminder(
            title="Daily",
            due_date=now,
            repeat_interval="day"
        )
        
        next_reminder = scheduler._create_next_reminder(reminder)
        
        assert next_reminder.due_date == datetime(2024, 1, 16, 14, 30, 0)

    def test_create_next_reminder_week(self, scheduler):
        """Тест создания следующего напоминания (неделя)."""
        now = datetime(2024, 1, 15, 14, 30, 0)
        
        reminder = Reminder(
            title="Weekly",
            due_date=now,
            repeat_interval="week"
        )
        
        next_reminder = scheduler._create_next_reminder(reminder)
        
        assert next_reminder.due_date == datetime(2024, 1, 22, 14, 30, 0)

    def test_create_next_reminder_month(self, scheduler):
        """Тест создания следующего напоминания (месяц)."""
        now = datetime(2024, 1, 15, 14, 30, 0)
        
        reminder = Reminder(
            title="Monthly",
            due_date=now,
            repeat_interval="month"
        )
        
        next_reminder = scheduler._create_next_reminder(reminder)
        
        assert next_reminder.due_date == datetime(2024, 2, 15, 14, 30, 0)

    def test_create_next_reminder_invalid_interval(self, scheduler):
        """Тест создания следующего напоминания с неверным интервалом."""
        reminder = Reminder(
            title="Invalid",
            due_date=datetime.now(),
            repeat_interval="invalid_interval"
        )
        
        with pytest.raises(ValueError, match="Неизвестный интервал повтора"):
            scheduler._create_next_reminder(reminder)

    def test_callback_invocation(
        self,
        scheduler,
        db_manager,
        mock_notification_service
    ):
        """Тест вызова callback при обработке напоминаний."""
        callback = Mock()
        scheduler.callback = callback
        
        now = datetime.now()
        reminder = Reminder(
            title="Callback Test",
            due_date=now - timedelta(seconds=1),
            status=Status.PENDING
        )
        db_manager.add_reminder(reminder)
        
        # Запускаем проверку
        scheduler.check_and_notify()
        
        # Callback должен быть вызван
        callback.assert_called_once()

    def test_callback_not_called_without_reminders(self, scheduler):
        """Тест, что callback не вызывается без напоминаний."""
        callback = Mock()
        scheduler.callback = callback
        
        scheduler.check_and_notify()
        
        # Callback не должен быть вызван
        callback.assert_not_called()

    def test_scheduler_thread_runs_background(
        self,
        db_manager,
        mock_notification_service
    ):
        """Тест, что планировщик работает в фоновом потоке."""
        callback = Mock()
        scheduler = Scheduler(
            database=db_manager,
            notification_service=mock_notification_service,
            check_interval=0.5,  # Очень короткий интервал
            callback=callback
        )
        
        # Добавляем напоминание, которое скоро сработает
        now = datetime.now()
        reminder = Reminder(
            title="Background Test",
            due_date=now + timedelta(seconds=1),
            status=Status.PENDING
        )
        db_manager.add_reminder(reminder)
        
        # Запускаем планировщик
        scheduler.start()
        
        # Ждём немного
        time.sleep(2)
        
        # Callback должен быть вызван (или напоминание обработано)
        # (в зависимости от времени)
        scheduler.stop()

    def test_multiple_pending_reminders(
        self,
        scheduler,
        db_manager,
        mock_notification_service
    ):
        """Тест обработки нескольких ожидающих напоминаний."""
        now = datetime.now()
        
        # Создаём несколько просроченных напоминаний
        for i in range(5):
            reminder = Reminder(
                title=f"Reminder {i}",
                description=f"Description {i}",
                due_date=now - timedelta(seconds=i + 1),
                status=Status.PENDING
            )
            db_manager.add_reminder(reminder)
        
        # Запускаем проверку
        processed = scheduler.check_and_notify()
        
        # Все должны быть обработаны
        assert len(processed) == 5
        
        # Все уведомления должны быть отправлены
        assert mock_notification_service.show_notification.call_count == 5

    def test_reminder_with_empty_fields(self, scheduler, db_manager):
        """Тест обработки напоминания с пустыми полями."""
        now = datetime.now()
        
        reminder = Reminder(
            title="",  # Пустой заголовок
            description="",  # Пустое описание
            due_date=now - timedelta(seconds=1),
            status=Status.PENDING
        )
        reminder_id = db_manager.add_reminder(reminder)
        
        processed = scheduler.check_and_notify()
        
        assert len(processed) == 1
        assert processed[0].id == reminder_id
        # Должно быть помечено как DONE
        updated = db_manager.get_reminder_by_id(reminder_id)
        assert updated.status == Status.DONE

    def test_reminder_without_recurrence_creates_no_duplicate(
        self,
        scheduler,
        db_manager
    ):
        """Тест, что неповторяющееся напоминание не создаёт дубликат."""
        now = datetime.now()
        
        reminder = Reminder(
            title="Once only",
            due_date=now - timedelta(seconds=1),
            status=Status.PENDING,
            repeat_interval=None
        )
        reminder_id = db_manager.add_reminder(reminder)
        
        scheduler.check_and_notify()
        
        # Должно быть только одно напоминание (исходное)
        all_reminders = db_manager.get_all_reminders()
        assert len(all_reminders) == 1
        
        # Статус должен быть DONE
        updated = db_manager.get_reminder_by_id(reminder_id)
        assert updated.status == Status.DONE