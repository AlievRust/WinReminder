"""Тесты для модели Reminder."""

import pytest
from datetime import datetime, timedelta

import sys
from pathlib import Path

# Добавляем src в путь для импортов
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from core.reminder import Reminder, Status


class TestReminder:
    """Тесты для класса Reminder."""

    def test_reminder_creation(self):
        """Тест создания напоминания."""
        reminder = Reminder(
            id=1,
            title="Test Reminder",
            description="Test description",
            due_date=datetime(2024, 1, 15, 14, 30),
            status=Status.PENDING,
            repeat_interval="day"
        )
        
        assert reminder.id == 1
        assert reminder.title == "Test Reminder"
        assert reminder.description == "Test description"
        assert reminder.status == Status.PENDING
        assert reminder.repeat_interval == "day"

    def test_reminder_defaults(self):
        """Тест значений по умолчанию."""
        reminder = Reminder()
        
        assert reminder.id is None
        assert reminder.title == ""
        assert reminder.description == ""
        assert reminder.status == Status.PENDING
        assert reminder.repeat_interval is None
        assert isinstance(reminder.due_date, datetime)
        assert isinstance(reminder.created_at, datetime)

    def test_is_overdue(self):
        """Тест проверки просрочки."""
        past_date = datetime.now() - timedelta(hours=1)
        future_date = datetime.now() + timedelta(hours=1)
        
        # Просроченное
        overdue_reminder = Reminder(due_date=past_date, status=Status.PENDING)
        assert overdue_reminder.is_overdue() is True
        
        # Не просроченное
        future_reminder = Reminder(due_date=future_date, status=Status.PENDING)
        assert future_reminder.is_overdue() is False
        
        # Выполненное (не должно быть просрочено)
        done_reminder = Reminder(due_date=past_date, status=Status.DONE)
        assert done_reminder.is_overdue() is False

    def test_is_recurring(self):
        """Тест проверки повторения."""
        recurring_reminder = Reminder(repeat_interval="day")
        assert recurring_reminder.is_recurring() is True
        
        non_recurring_reminder = Reminder(repeat_interval=None)
        assert non_recurring_reminder.is_recurring() is False

    def test_to_dict(self):
        """Тест преобразования в словарь."""
        due_date = datetime(2024, 1, 15, 14, 30)
        reminder = Reminder(
            id=1,
            title="Test",
            due_date=due_date,
            status=Status.PENDING
        )
        
        data = reminder.to_dict()
        
        assert data["id"] == 1
        assert data["title"] == "Test"
        assert data["due_date"] == "2024-01-15T14:30:00"
        assert data["status"] == "pending"

    def test_from_dict(self):
        """Тест создания из словаря."""
        data = {
            "id": 1,
            "title": "Test",
            "description": "Desc",
            "due_date": "2024-01-15T14:30:00",
            "status": "pending",
            "repeat_interval": "day",
            "created_at": "2024-01-01T10:00:00"
        }
        
        reminder = Reminder.from_dict(data)
        
        assert reminder.id == 1
        assert reminder.title == "Test"
        assert reminder.description == "Desc"
        assert reminder.due_date == datetime(2024, 1, 15, 14, 30)
        assert reminder.status == Status.PENDING
        assert reminder.repeat_interval == "day"


class TestStatus:
    """Тесты для enum Status."""

    def test_display_name(self):
        """Тест отображаемых имён статусов."""
        assert Status.PENDING.display_name() == "Ожидает"
        assert Status.DONE.display_name() == "Готово"
        assert Status.OVERDUE.display_name() == "Просрочено"
        assert Status.CANCELLED.display_name() == "Отменено"

    def test_from_display_name(self):
        """Тест получения статуса из русского названия."""
        assert Status.from_display_name("Ожидает") == Status.PENDING
        assert Status.from_display_name("Готово") == Status.DONE
        assert Status.from_display_name("Просрочено") == Status.OVERDUE
        assert Status.from_display_name("Отменено") == Status.CANCELLED
        assert Status.from_display_name("Unknown") == Status.PENDING  # Default