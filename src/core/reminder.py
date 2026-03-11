"""Модель Reminder для приложения Reminder."""

from datetime import datetime
from enum import Enum
from typing import Optional


class Status(Enum):
    """Статусы напоминаний."""
    PENDING = "pending"  # Ожидает
    DONE = "done"  # Готово
    OVERDUE = "overdue"  # Просрочено
    CANCELLED = "cancelled"  # Отменено

    def display_name(self) -> str:
        """Отображаемое имя статуса на русском."""
        display_map = {
            Status.PENDING: "Ожидает",
            Status.DONE: "Готово",
            Status.OVERDUE: "Просрочено",
            Status.CANCELLED: "Отменено"
        }
        return display_map[self]

    @classmethod
    def from_display_name(cls, name: str) -> "Status":
        """Получить статус из русского названия."""
        reverse_map = {
            "Ожидает": cls.PENDING,
            "Готово": cls.DONE,
            "Просрочено": cls.OVERDUE,
            "Отменено": cls.CANCELLED
        }
        return reverse_map.get(name, cls.PENDING)


class Reminder:
    """Класс, представляющий напоминание."""

    def __init__(
        self,
        id: Optional[int] = None,
        title: str = "",
        description: str = "",
        due_date: Optional[datetime] = None,
        status: Status = Status.PENDING,
        repeat_interval: Optional[str] = None,
        created_at: Optional[datetime] = None
    ):
        """
        Инициализация напоминания.

        Args:
            id: Уникальный идентификатор (None для нового напоминания)
            title: Заголовок напоминания
            description: Описание напоминания
            due_date: Дата и время срабатывания
            status: Статус напоминания
            repeat_interval: Интервал повтора (hour, day, week, month или None)
            created_at: Дата создания
        """
        self.id = id
        self.title = title
        self.description = description
        self.due_date = due_date or datetime.now()
        self.status = status
        self.repeat_interval = repeat_interval
        self.created_at = created_at or datetime.now()

    def is_overdue(self) -> bool:
        """Проверить, просрочено ли напоминание."""
        return self.due_date < datetime.now() and self.status == Status.PENDING

    def is_recurring(self) -> bool:
        """Проверить, является ли напоминание повторяющимся."""
        return self.repeat_interval is not None

    def __repr__(self) -> str:
        """Строковое представление."""
        return (
            f"Reminder(id={self.id}, title='{self.title}', "
            f"due_date={self.due_date.isoformat()}, status={self.status.value})"
        )

    def to_dict(self) -> dict:
        """Преобразовать в словарь."""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "status": self.status.value,
            "repeat_interval": self.repeat_interval,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Reminder":
        """Создать объект из словаря."""
        return cls(
            id=data.get("id"),
            title=data.get("title", ""),
            description=data.get("description", ""),
            due_date=datetime.fromisoformat(data["due_date"]) if data.get("due_date") else None,
            status=Status(data.get("status", "pending")),
            repeat_interval=data.get("repeat_interval"),
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else None
        )