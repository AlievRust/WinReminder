"""Тесты для DatabaseManager."""

import pytest
import tempfile
import shutil
from datetime import datetime, timedelta

import sys
from pathlib import Path

# Добавляем src в путь для импортов
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from core.database import DatabaseManager
from core.reminder import Reminder, Status


@pytest.fixture
def temp_db_path(tmp_path):
    """Фикстура для создания временной базы данных."""
    db_path = tmp_path / "test_reminders.db"
    yield str(db_path)
    # Очистка происходит автоматически через tmp_path


@pytest.fixture
def db_manager(temp_db_path):
    """Фикстура для создания менеджера базы данных."""
    db = DatabaseManager(temp_db_path)
    yield db
    db.close()


@pytest.fixture
def sample_reminder():
    """Фикстура с примером напоминания."""
    return Reminder(
        title="Test Reminder",
        description="Test description",
        due_date=datetime(2024, 1, 15, 14, 30),
        status=Status.PENDING,
        repeat_interval="day"
    )


class TestDatabaseManager:
    """Тесты для DatabaseManager."""

    def test_database_initialization(self, db_manager):
        """Тест инициализации базы данных."""
        # База должна быть создана и схема должна существовать
        reminders = db_manager.get_all_reminders()
        assert isinstance(reminders, list)
        assert len(reminders) == 0

    def test_add_reminder(self, db_manager, sample_reminder):
        """Тест добавления напоминания."""
        reminder_id = db_manager.add_reminder(sample_reminder)
        
        assert reminder_id is not None
        assert isinstance(reminder_id, int)
        assert reminder_id > 0
        
        # Проверяем, что напоминание сохранено
        saved_reminder = db_manager.get_reminder_by_id(reminder_id)
        assert saved_reminder is not None
        assert saved_reminder.title == sample_reminder.title
        assert saved_reminder.description == sample_reminder.description

    def test_get_all_reminders(self, db_manager, sample_reminder):
        """Тест получения всех напоминаний."""
        # Добавляем несколько напоминаний
        reminder1 = Reminder(title="Reminder 1", due_date=datetime.now())
        reminder2 = Reminder(title="Reminder 2", due_date=datetime.now() + timedelta(hours=1))
        reminder3 = Reminder(title="Reminder 3", due_date=datetime.now() + timedelta(hours=2))
        
        id1 = db_manager.add_reminder(reminder1)
        id2 = db_manager.add_reminder(reminder2)
        id3 = db_manager.add_reminder(reminder3)
        
        all_reminders = db_manager.get_all_reminders()
        
        assert len(all_reminders) == 3
        titles = [r.title for r in all_reminders]
        assert "Reminder 1" in titles
        assert "Reminder 2" in titles
        assert "Reminder 3" in titles

    def test_get_reminders_by_status(self, db_manager):
        """Тест фильтрации по статусу."""
        reminder1 = Reminder(title="Pending", status=Status.PENDING, due_date=datetime.now())
        reminder2 = Reminder(title="Done", status=Status.DONE, due_date=datetime.now())
        reminder3 = Reminder(title="Another Pending", status=Status.PENDING, due_date=datetime.now())
        
        db_manager.add_reminder(reminder1)
        db_manager.add_reminder(reminder2)
        db_manager.add_reminder(reminder3)
        
        pending = db_manager.get_reminders_by_status(Status.PENDING)
        done = db_manager.get_reminders_by_status(Status.DONE)
        
        assert len(pending) == 2
        assert len(done) == 1
        assert all(r.status == Status.PENDING for r in pending)
        assert all(r.status == Status.DONE for r in done)

    def test_get_reminder_by_id(self, db_manager, sample_reminder):
        """Тест получения напоминания по ID."""
        reminder_id = db_manager.add_reminder(sample_reminder)
        
        found = db_manager.get_reminder_by_id(reminder_id)
        assert found is not None
        assert found.id == reminder_id
        assert found.title == sample_reminder.title
        
        # Проверяем несуществующий ID
        not_found = db_manager.get_reminder_by_id(99999)
        assert not_found is None

    def test_update_status(self, db_manager, sample_reminder):
        """Тест обновления статуса."""
        reminder_id = db_manager.add_reminder(sample_reminder)
        
        # Обновляем статус
        result = db_manager.update_status(reminder_id, Status.DONE)
        assert result is True
        
        # Проверяем обновление
        updated = db_manager.get_reminder_by_id(reminder_id)
        assert updated.status == Status.DONE
        
        # Проверяем обновление несуществующего напоминания
        result = db_manager.update_status(99999, Status.DONE)
        assert result is False

    def test_delete_reminder(self, db_manager, sample_reminder):
        """Тест удаления напоминания."""
        reminder_id = db_manager.add_reminder(sample_reminder)
        
        # Удаляем
        result = db_manager.delete_reminder(reminder_id)
        assert result is True
        
        # Проверяем удаление
        deleted = db_manager.get_reminder_by_id(reminder_id)
        assert deleted is None
        
        # Проверяем удаление несуществующего напоминания
        result = db_manager.delete_reminder(99999)
        assert result is False

    def test_get_pending_reminders(self, db_manager):
        """Тест получения ожидающих напоминаний до указанного времени."""
        now = datetime.now()
        
        # Создаём напоминания в разное время
        past_reminder = Reminder(
            title="Past",
            due_date=now - timedelta(hours=1),
            status=Status.PENDING
        )
        current_reminder = Reminder(
            title="Now",
            due_date=now,
            status=Status.PENDING
        )
        future_reminder = Reminder(
            title="Future",
            due_date=now + timedelta(hours=1),
            status=Status.PENDING
        )
        
        db_manager.add_reminder(past_reminder)
        db_manager.add_reminder(current_reminder)
        db_manager.add_reminder(future_reminder)
        
        pending = db_manager.get_pending_reminders(now)
        
        assert len(pending) == 2
        titles = [r.title for r in pending]
        assert "Past" in titles
        assert "Now" in titles
        assert "Future" not in titles

    def test_update_overdue_reminders(self, db_manager):
        """Тест автоматического обновления просроченных напоминаний."""
        now = datetime.now()
        
        # Создаём просроченное и будущее напоминания
        overdue = Reminder(
            title="Overdue",
            due_date=now - timedelta(hours=1),
            status=Status.PENDING
        )
        future = Reminder(
            title="Future",
            due_date=now + timedelta(hours=1),
            status=Status.PENDING
        )
        
        db_manager.add_reminder(overdue)
        db_manager.add_reminder(future)
        
        # Обновляем просроченные
        count = db_manager.update_overdue_reminders()
        
        # Должно быть обновлено 1 напоминание
        assert count >= 1
        
        # Проверяем статусы
        updated_overdue = db_manager.get_reminders_by_status(Status.OVERDUE)
        assert len(updated_overdue) >= 1
        
        # Будущее должно остаться PENDING
        future_updated = db_manager.get_reminders_by_status(Status.PENDING)
        assert len(future_updated) >= 1

    def test_reminder_persistence(self, db_manager, sample_reminder):
        """Тест сохранения данных между сессиями."""
        # Добавляем напоминание
        reminder_id = db_manager.add_reminder(sample_reminder)
        
        # Закрываем и открываем заново
        db_manager.close()
        new_db = DatabaseManager(db_manager.db_path)
        
        # Проверяем, что данные сохранились
        saved = new_db.get_reminder_by_id(reminder_id)
        assert saved is not None
        assert saved.title == sample_reminder.title
        assert saved.description == sample_reminder.description
        assert saved.repeat_interval == sample_reminder.repeat_interval

    def test_recurrence_intervals(self, db_manager):
        """Тест сохранения интервалов повторения."""
        intervals = ["hour", "day", "week", "month", None]
        
        for interval in intervals:
            reminder = Reminder(
                title=f"Interval {interval or 'None'}",
                due_date=datetime.now(),
                repeat_interval=interval
            )
            reminder_id = db_manager.add_reminder(reminder)
            
            saved = db_manager.get_reminder_by_id(reminder_id)
            assert saved.repeat_interval == interval