"""Главное окно приложения Reminder."""

import tkinter as tk
from tkinter import ttk, messagebox


class MainWindow:
    """Главное окно со списком напоминаний."""

    def __init__(self, root: tk.Tk):
        """
        Инициализация главного окна.

        Args:
            root: Корневой объект Tkinter
        """
        self.root = root
        self.setup_ui()
        # TODO: Подключить сервисы и загрузить данные

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

    def on_add(self):
        """Обработчик кнопки Добавить."""
        # TODO: Открыть диалог добавления
        messagebox.showinfo("В разработке", "Функция добавления будет реализована")

    def on_done(self):
        """Обработчик кнопки Готово."""
        # TODO: Отметить выбранное напоминание как выполненное
        messagebox.showinfo("В разработке", "Функция будет реализована")

    def on_cancel(self):
        """Обработчик кнопки Отменить."""
        # TODO: Отменить выбранное напоминание
        messagebox.showinfo("В разработке", "Функция будет реализована")

    def on_delete(self):
        """Обработчик кнопки Удалить."""
        # TODO: Удалить выбранное напоминание
        messagebox.showinfo("В разработке", "Функция будет реализована")

    def on_test_notification(self):
        """Обработчик кнопки Тест уведомления."""
        # TODO: Показать тестовое уведомление
        messagebox.showinfo("В разработке", "Функция будет реализована")

    def on_filter_change(self, event):
        """Обработчик изменения фильтра."""
        # TODO: Обновить список напоминаний по фильтру
        pass

    def refresh_list(self):
        """Обновить список напоминаний."""
        # TODO: Загрузить напоминания из БД и отобразить
        pass