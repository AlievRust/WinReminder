"""Главное окно приложения Reminder."""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional, List
from datetime import datetime

from core.database import DatabaseManager
from core.reminder import Reminder, Status
from services.notification import get_notification_service


class MainWindow:
    """Главное окно со списком напоминаний."""

    POLL_INTERVAL = 30000  # 30 секунд в миллисекундах

    def __init__(self, root: tk.Tk):
        """
        Инициализация главного окна.

        Args:
            root: Корневой объект Tkinter
        """
        self.root = root
        self.db: DatabaseManager = DatabaseManager()
        self.notification_service = get_notification_service()
        
        self.setup_ui()
        self.refresh_list()
        
        # Запуск автообновления списка
        self.root.after(self.POLL_INTERVAL, self.auto_refresh)

    def setup_ui(self):
        """Настройка пользовательского интерфейса."""
        # Панель инструментов
        toolbar = ttk.Frame(self.root, padding=5)
        toolbar.pack(side=tk.TOP, fill=tk.X)

        ttk.Button(toolbar, text="Добавить", command=self.on_add).pack(side=tk.LEFT)
        ttk.Button(toolbar, text="Готово", command=self.on_done).pack(side=tk.LEFT, padx=5)
        ttk.Button(toolbar, text="Отменить", command=self.on_cancel).pack(side=tk.LEFT)
        ttk.Button(toolbar, text="Удалить", command=self.on_delete).pack(side=tk.LEFT, padx=5)

        # Фильтр по статусу
        ttk.Label(toolbar, text="Фильтр:").pack(side=tk.LEFT, padx=10)
        self.filter_var = tk.StringVar(value="Все")
        filter_combo = ttk.Combobox(
            toolbar,
            textvariable=self.filter_var,
            values=["Все", "Ожидает", "Готово", "Просрочено", "Отменено"],
            state="readonly",
            width=10
        )
        filter_combo.pack(side=tk.LEFT)
        filter_combo.bind("<<ComboboxSelected>>", self.on_filter_change)

        ttk.Button(toolbar, text="Тест уведомления", command=self.on_test_notification).pack(side=tk.RIGHT)

        # Список напоминаний
        tree_frame = ttk.Frame(self.root, padding=5)
        tree_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        columns = ("title", "due_date", "status", "repeat")
        self.tree = ttk.Treeview(tree_frame, columns=columns, show="headings")
        
        self.tree.heading("title", text="Заголовок")
        self.tree.heading("due_date", text="Дата/время")
        self.tree.heading("status", text="Статус")
        self.tree.heading("repeat", text="Повторение")

        self.tree.column("title", width=250)
        self.tree.column("due_date", width=150)
        self.tree.column("status", width=100)
        self.tree.column("repeat", width=100)

        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Статусная строка
        self.status_var = tk.StringVar(value="Готов")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def get_filtered_reminders(self) -> List[Reminder]:
        """
        Получить список напоминаний с учётом фильтра.

        Returns:
            Список отфильтрованных напоминаний
        """
        # Сначала обновляем просроченные
        self.db.update_overdue_reminders()
        
        filter_value = self.filter_var.get()
        
        if filter_value == "Все":
            reminders = self.db.get_all_reminders()
        else:
            status = Status.from_display_name(filter_value)
            reminders = self.db.get_reminders_by_status(status)
        
        return reminders

    def refresh_list(self):
        """Обновить список напоминаний в UI."""
        # Очистить дерево
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Получить отфильтрованные напоминания
        reminders = self.get_filtered_reminders()
        
        # Заполнить дерево
        for reminder in reminders:
            due_str = reminder.due_date.strftime("%d.%m.%Y %H:%M")
            status_str = reminder.status.display_name()
            repeat_str = self._get_repeat_display(reminder.repeat_interval)
            
            self.tree.insert(
                "",
                tk.END,
                values=(reminder.title, due_str, status_str, repeat_str),
                tags=(str(reminder.id),)
            )
        
        # Обновить статусную строку
        self.status_var.set(f"Всего напоминаний: {len(reminders)}")

    def _get_repeat_display(self, repeat_interval: Optional[str]) -> str:
        """
        Получить отображаемое значение повтора.

        Args:
            repeat_interval: Интервал повтора

        Returns:
            Строка для отображения
        """
        if not repeat_interval:
            return "Нет"
        
        repeat_map = {
            "hour": "Час",
            "day": "День",
            "week": "Неделя",
            "month": "Месяц"
        }
        return repeat_map.get(repeat_interval, repeat_interval)

    def get_selected_reminder_id(self) -> Optional[int]:
        """
        Получить ID выбранного напоминания.

        Returns:
            ID напоминания или None, если ничего не выбрано
        """
        selection = self.tree.selection()
        if not selection:
            return None
        
        item = self.tree.item(selection[0])
        reminder_id = int(item["tags"][0])
        return reminder_id

    def on_add(self):
        """
        Обработчик кнопки Добавить.
        Открывает диалог добавления напоминания.
        """
        from gui.add_dialog import AddReminderDialog
        
        dialog = AddReminderDialog(self.root)
        self.root.wait_window(dialog.window)
        
        if dialog.result:
            # Создать объект Reminder из данных диалога
            reminder = Reminder(
                title=dialog.result["title"],
                description=dialog.result["description"],
                due_date=dialog.result["due_date"],
                repeat_interval=dialog.result["repeat_interval"]
            )
            
            # Сохранить в БД
            self.db.add_reminder(reminder)
            self.refresh_list()

    def on_done(self):
        """
        Обработчик кнопки Готово.
        Помечает выбранное напоминание как выполненное.
        """
        reminder_id = self.get_selected_reminder_id()
        if reminder_id is None:
            messagebox.showwarning("Предупреждение", "Выберите напоминание из списка")
            return
        
        if messagebox.askyesno("Подтверждение", "Отметить напоминание как выполненное?"):
            self.db.update_status(reminder_id, Status.DONE)
            self.refresh_list()

    def on_cancel(self):
        """
        Обработчик кнопки Отменить.
        Отменяет выбранное напоминание.
        """
        reminder_id = self.get_selected_reminder_id()
        if reminder_id is None:
            messagebox.showwarning("Предупреждение", "Выберите напоминание из списка")
            return
        
        if messagebox.askyesno("Подтверждение", "Отменить выбранное напоминание?"):
            self.db.update_status(reminder_id, Status.CANCELLED)
            self.refresh_list()

    def on_delete(self):
        """
        Обработчик кнопки Удалить.
        Удаляет выбранное напоминание.
        """
        reminder_id = self.get_selected_reminder_id()
        if reminder_id is None:
            messagebox.showwarning("Предупреждение", "Выберите напоминание из списка")
            return
        
        if messagebox.askyesno("Подтверждение", "Удалить выбранное напоминание?"):
            self.db.delete_reminder(reminder_id)
            self.refresh_list()

    def on_test_notification(self):
        """
        Обработчик кнопки Тест уведомления.
        Показывает тестовое уведомление.
        При успешной отправке не показывает всплывающее сообщение.
        """
        success = self.notification_service.test_notification()
        if not success:
            messagebox.showerror("Ошибка", "Не удалось отправить уведомление")

    def on_filter_change(self, event):
        """
        Обработчик изменения фильтра.
        Обновляет список напоминаний в соответствии с выбранным фильтром.
        """
        self.refresh_list()

    def auto_refresh(self):
        """
        Автоматическое обновление списка (вызывается каждые 30 секунд).
        """
        self.refresh_list()
        # Запланировать следующее обновление
        self.root.after(self.POLL_INTERVAL, self.auto_refresh)
