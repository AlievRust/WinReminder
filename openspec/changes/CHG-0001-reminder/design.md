# Design: Reminder Application (change-001)

## Архитектура

### Высокий уровень
```
┌─────────────────────────────────────┐
│          GUI Layer (Tkinter)        │
│  ┌──────────┐  ┌──────────────────┐ │
│  │ MainWindow│  │  AddReminderDialog│ │
│  └──────────┘  └──────────────────┘ │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│        Service Layer               │
│  ┌──────────┐  ┌──────────────────┐ │
│  │ReminderService│ │ NotificationService│ │
│  └────┬─────┘  └──────────────────┘ │
└───────┼──────────────────────────────┘
        │
┌───────▼──────────────────────────────┐
│        Data Layer                    │
│  ┌──────────┐  ┌──────────────────┐ │
│  │DatabaseManager│ │   ReminderModel   │ │
│  └──────────┘  └──────────────────┘ │
└──────────────────────────────────────┘
```

### Структура проекта
```
reminder/
├── pyproject.toml
├── README.md
├── src/
│   ├── __init__.py
│   ├── main.py                 # Точка входа
│   ├── gui/                    # Tkinter интерфейс
│   │   ├── __init__.py
│   │   ├── main_window.py      # Главное окно со списком
│   │   ├── add_dialog.py       # Диалог добавления
│   │   └── widgets.py          # Кастомные виджеты
│   ├── core/                   # Бизнес-логика
│   │   ├── __init__.py
│   │   ├── database.py         # SQLite3 менеджер
│   │   ├── reminder.py         # Модель Reminder
│   │   └── scheduler.py        # Проверка времени (threading)
│   └── services/               # Сервисы
│       ├── __init__.py
│       └── notification.py     # Обёртка над plyer
├── data/
│   └── reminders.db            # SQLite БД
└── tests/
    ├── test_database.py
    ├── test_reminder.py
    └── test_scheduler.py
```

## Схема базы данных (SQLite3)

### Таблица reminders
```sql
CREATE TABLE reminders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    description TEXT,
    due_date TEXT NOT NULL,        -- ISO 8601: "2024-01-15T14:30:00"
    status TEXT NOT NULL DEFAULT 'pending',
    repeat_interval TEXT,          -- NULL, 'hour', 'day', 'week', 'month'
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX idx_due_date ON reminders(due_date);
CREATE INDEX idx_status ON reminders(status);
```

## Ключевые компоненты

### Reminder Model
```python
class Reminder:
    id: int
    title: str
    description: str
    due_date: datetime
    status: Status  # Enum: PENDING, DONE, OVERDUE, CANCELLED
    repeat_interval: Optional[str]
    created_at: datetime
```

### DatabaseManager
- `add_reminder(reminder: Reminder) -> int`
- `get_all_reminders() -> List[Reminder]`
- `get_reminders_by_status(status: Status) -> List[Reminder]`
- `update_status(id: int, status: Status) -> bool`
- `delete_reminder(id: int) -> bool`
- `update_overdue_reminders() -> int`

### Scheduler (Threading)
- Фоновый поток, проверяющий каждые 10 секунд
- `check_and_notify()` - ищет due <= now и status = PENDING
- При нахождении: вызывает NotificationService и обновляет статус
- Для повторяющихся: создаёт новое напоминание с новой датой

### NotificationService
- `show_notification(title: str, message: str)` - использует plyer
- `test_notification()` - для кнопки теста

## GUI компоненты

### MainWindow
- Treeview для списка напоминаний с колонками:
  - Заголовок | Дата/время | Статус | Повторение
- Фильтр по статусу (Combobox)
- Кнопки: Добавить, Удалить, Готово, Отменить, Тест уведомления
- Обновление списка каждые 30 секунд или по событию

### AddReminderDialog
- Поля: Title (Entry), Description (Text), DateTime (с календарём)
- Быстрые кнопки: +1 мин, +15 мин, +30 мин, +1 час
- Повторение: Combobox (Нет, Час, День, Неделя, Месяц)

## Поток выполнения

### Добавление напоминания
1. Пользователь открывает AddReminderDialog
2. Заполняет поля, выбирает быстрое время или календарь
3. Нажимает "Сохранить"
4. GUI → ReminderService.add()
5. Service → DatabaseManager.add_reminder()
6. GUI обновляет список

### Срабатывание напоминания
1. Scheduler проверяет каждые 10 сек
2. Находит due <= now, status = PENDING
3. Вызывает NotificationService.show()
4. Если repeat_interval: создаёт новое напоминание
5. Обновляет статус текущего на DONE или оставляет PENDING (для повторяющихся)
6. GUI обновляет список (через callback или polling)

## Обработка повторяющихся напоминаний

### Логика
```
if reminder.repeat_interval:
    next_date = reminder.due_date + interval
    new_reminder = Reminder(
        title=reminder.title,
        description=reminder.description,
        due_date=next_date,
        repeat_interval=reminder.repeat_interval
    )
    database.add_reminder(new_reminder)
```

### Интервалы
- hour: + timedelta(hours=1)
- day: + timedelta(days=1)
- week: + timedelta(weeks=1)
- month: + relativedelta(months=1)  #需要 dateutil