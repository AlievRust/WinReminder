"""Диалог добавления напоминания."""

import tkinter as tk
from tkinter import ttk
from datetime import datetime, timedelta


class AddReminderDialog:
    """Диалог для создания нового напоминания."""

    def __init__(self, parent):
        """
        Инициализация диалога.

        Args:
            parent: Родительское окно
        """
        self.result = None
        self.window = tk.Toplevel(parent)
        self.window.title("Добавить напоминание")
        self.window.geometry("500x500")
        self.window.transient(parent)
        self.window.grab_set()

        self.setup_ui()
        self.set_default_datetime()

    def setup_ui(self):
        """Настройка пользовательского интерфейса."""
        main_frame = ttk.Frame(self.window, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Заголовок
        ttk.Label(main_frame, text="Заголовок:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.title_entry = ttk.Entry(main_frame, width=40)
        self.title_entry.grid(row=0, column=1, sticky=tk.EW, pady=5)

        # Описание
        ttk.Label(main_frame, text="Описание:").grid(row=1, column=0, sticky=tk.NW, pady=5)
        self.description_text = tk.Text(main_frame, width=40, height=5, wrap=tk.WORD)
        self.description_text.grid(row=1, column=1, sticky=tk.EW, pady=5)

        # Дата и время
        date_frame = ttk.Frame(main_frame)
        date_frame.grid(row=2, column=0, columnspan=2, sticky=tk.EW, pady=10)

        ttk.Label(date_frame, text="Дата и время:").pack(side=tk.LEFT)
        self.datetime_var = tk.StringVar()
        self.datetime_entry = ttk.Entry(date_frame, textvariable=self.datetime_var, width=25)
        self.datetime_entry.pack(side=tk.LEFT, padx=5)

        # Быстрые кнопки
        ttk.Button(date_frame, text="+1 мин", command=lambda: self.add_time(1)).pack(side=tk.LEFT, padx=2)
        ttk.Button(date_frame, text="+15 мин", command=lambda: self.add_time(15)).pack(side=tk.LEFT, padx=2)
        ttk.Button(date_frame, text="+30 мин", command=lambda: self.add_time(30)).pack(side=tk.LEFT, padx=2)
        ttk.Button(date_frame, text="+1 час", command=lambda: self.add_time(60)).pack(side=tk.LEFT, padx=2)

        # Повторение
        ttk.Label(main_frame, text="Повторение:").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.repeat_var = tk.StringVar(value="Нет")
        repeat_combo = ttk.Combobox(
            main_frame,
            textvariable=self.repeat_var,
            values=["Нет", "Час", "День", "Неделя", "Месяц"],
            state="readonly",
            width=20
        )
        repeat_combo.grid(row=3, column=1, sticky=tk.W, pady=5)

        # Кнопки
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=4, column=0, columnspan=2, pady=20)

        ttk.Button(button_frame, text="Сохранить", command=self.on_save).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Отмена", command=self.on_cancel).pack(side=tk.LEFT, padx=5)

    def set_default_datetime(self):
        """Установить дату/время по умолчанию (сейчас)."""
        now = datetime.now()
        self.datetime_var.set(now.strftime("%Y-%m-%d %H:%M"))

    def add_time(self, minutes):
        """Добавить время к текущей дате."""
        try:
            current_str = self.datetime_var.get()
            current = datetime.strptime(current_str, "%Y-%m-%d %H:%M")
            new_time = current + timedelta(minutes=minutes)
            self.datetime_var.set(new_time.strftime("%Y-%m-%d %H:%M"))
        except ValueError:
            self.set_default_datetime()
            self.add_time(minutes)

    def on_save(self):
        """Обработчик кнопки Сохранить."""
        title = self.title_entry.get().strip()
        if not title:
            tk.messagebox.showwarning("Ошибка", "Введите заголовок")
            return

        try:
            due_date = datetime.strptime(self.datetime_var.get(), "%Y-%m-%d %H:%M")
        except ValueError:
            tk.messagebox.showwarning("Ошибка", "Неверный формат даты/времени")
            return

        repeat_map = {
            "Нет": None,
            "Час": "hour",
            "День": "day",
            "Неделя": "week",
            "Месяц": "month"
        }

        self.result = {
            "title": title,
            "description": self.description_text.get("1.0", tk.END).strip(),
            "due_date": due_date,
            "repeat_interval": repeat_map[self.repeat_var.get()]
        }
        self.window.destroy()

    def on_cancel(self):
        """Обработчик кнопки Отмена."""
        self.window.destroy()