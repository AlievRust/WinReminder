"""Диалог добавления напоминания."""

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, timedelta

from gui.widgets import Calendar


class AddReminderDialog:
    """
    Диалог для создания нового напоминания.
    
    Диалог имеет фиксированный размер 550x680 пикселей, чтобы все элементы
    гарантированно помещались в окне без скроллирования.
    
    Использование:
        dialog = AddReminderDialog(parent)
        parent.wait_window(dialog.window)
        if dialog.result:
            title = dialog.result["title"]
            due_date = dialog.result["due_date"]
            # ... обработка данных
    """

    def __init__(self, parent):
        """
        Инициализация диалога.

        Args:
            parent: Родительское окно
        """
        self.result = None
        self.window = tk.Toplevel(parent)
        self.window.title("Добавить напоминание")
        self.window.geometry("550x680")
        self.window.resizable(False, False)  # Фиксированный размер
        self.window.transient(parent)
        self.window.grab_set()

        # Словарь для хранения введённых данных
        self.reminder_data = {
            "title": "",
            "description": "",
            "due_date": None,
            "repeat_interval": None
        }

        self.setup_ui()
        self.set_default_datetime()

    def setup_ui(self):
        """
        Настройка пользовательского интерфейса.
        Все элементы размещаются без скроллирования, так как окно имеет фиксированный размер.
        """
        # Основной контейнер (без скроллирования)
        main_frame = ttk.Frame(self.window, padding=15)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # ===== Заголовок =====
        title_frame = ttk.Frame(main_frame)
        title_frame.pack(fill=tk.X, pady=(0, 10))
        ttk.Label(title_frame, text="Заголовок:", font=('Arial', 9, 'bold')).pack(side=tk.LEFT)
        self.title_entry = ttk.Entry(title_frame, width=50)
        self.title_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(10, 0))

        # ===== Описание =====
        desc_frame = ttk.Frame(main_frame)
        desc_frame.pack(fill=tk.X, pady=(0, 15))
        ttk.Label(desc_frame, text="Описание:", font=('Arial', 9, 'bold')).pack(side=tk.TOP, anchor=tk.W)
        self.description_text = tk.Text(
            desc_frame, 
            width=60, 
            height=4, 
            wrap=tk.WORD,
            font=('Arial', 9)
        )
        self.description_text.pack(fill=tk.X, pady=(5, 0))

        # ===== Разделитель =====
        ttk.Separator(main_frame, orient='horizontal').pack(fill='x', pady=10)

        # ===== Дата и время =====
        datetime_frame = ttk.LabelFrame(main_frame, text="Дата и время", padding=10)
        datetime_frame.pack(fill=tk.X, pady=(0, 15))

        # Календарь
        calendar_frame = ttk.Frame(datetime_frame)
        calendar_frame.pack(side=tk.TOP, pady=(0, 10))
        
        self.calendar = Calendar(
            calendar_frame,
            callback=self._on_date_selected,
            selected_date=datetime.now()
        )
        self.calendar.pack()

        # Выбор времени
        time_frame = ttk.Frame(datetime_frame)
        time_frame.pack(fill=tk.X)
        
        ttk.Label(time_frame, text="Время:").pack(side=tk.LEFT)
        
        self.hours_var = tk.StringVar(value=datetime.now().strftime("%H"))
        self.minutes_var = tk.StringVar(value=datetime.now().strftime("%M"))
        
        hours_spin = ttk.Spinbox(
            time_frame,
            from_=0,
            to=23,
            width=3,
            textvariable=self.hours_var,
            format="%02.0f"
        )
        hours_spin.pack(side=tk.LEFT, padx=(10, 5))
        
        ttk.Label(time_frame, text=":").pack(side=tk.LEFT)
        
        minutes_spin = ttk.Spinbox(
            time_frame,
            from_=0,
            to=59,
            width=3,
            textvariable=self.minutes_var,
            format="%02.0f"
        )
        minutes_spin.pack(side=tk.LEFT, padx=5)

        # Быстрые кнопки времени
        quick_time_frame = ttk.Frame(datetime_frame)
        quick_time_frame.pack(fill=tk.X, pady=(10, 0))
        ttk.Label(quick_time_frame, text="Быстрая настройка:").pack(side=tk.LEFT)
        
        quick_buttons = [
            ("+1 мин", 1),
            ("+15 мин", 15),
            ("+30 мин", 30),
            ("+1 час", 60),
            ("+3 часа", 180),
            ("+1 день", 1440)
        ]
        
        for btn_text, minutes in quick_buttons:
            ttk.Button(
                quick_time_frame,
                text=btn_text,
                command=lambda m=minutes: self.add_time(m)
            ).pack(side=tk.LEFT, padx=2)

        # ===== Разделитель =====
        ttk.Separator(main_frame, orient='horizontal').pack(fill='x', pady=10)

        # ===== Повторение =====
        repeat_frame = ttk.Frame(main_frame)
        repeat_frame.pack(fill=tk.X, pady=(0, 20))
        ttk.Label(repeat_frame, text="Повторение:", font=('Arial', 9, 'bold')).pack(side=tk.LEFT)
        
        self.repeat_var = tk.StringVar(value="Нет")
        repeat_combo = ttk.Combobox(
            repeat_frame,
            textvariable=self.repeat_var,
            values=["Нет", "Час", "День", "Неделя", "Месяц"],
            state="readonly",
            width=15
        )
        repeat_combo.pack(side=tk.LEFT, padx=(10, 0))

        # ===== Кнопки действий =====
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=10)

        ttk.Button(
            button_frame, 
            text="Сохранить",
            command=self.on_save
        ).pack(side=tk.RIGHT, padx=(5, 0))
        
        ttk.Button(
            button_frame,
            text="Отмена",
            command=self.on_cancel
        ).pack(side=tk.RIGHT)

        # Привязка Enter к сохранению
        self.window.bind('<Return>', lambda e: self.on_save())
        self.window.bind('<Escape>', lambda e: self.on_cancel())

    def set_default_datetime(self):
        """Установить дату/время по умолчанию (сейчас)."""
        now = datetime.now()
        self.hours_var.set(now.strftime("%H"))
        self.minutes_var.set(now.strftime("%M"))
        self.reminder_data["due_date"] = now

    def _on_date_selected(self, selected_date: datetime):
        """
        Обработчик выбора даты в календаре.
        
        Args:
            selected_date: Выбранная дата
        """
        # Обновляем время из календаря, сохраняя выбранное время из спинбоксов
        try:
            hours = int(self.hours_var.get())
            minutes = int(self.minutes_var.get())
            
            # Комбинируем выбранную дату с выбранным временем
            combined = selected_date.replace(hour=hours, minute=minutes)
            self.reminder_data["due_date"] = combined
        except (ValueError, TypeError):
            # Если время некорректно, используем текущее
            self.reminder_data["due_date"] = selected_date

    def add_time(self, minutes: int):
        """
        Добавить время к текущей дате.
        
        Args:
            minutes: Количество минут для добавления
        """
        # Получаем текущую дату из календаря
        current_date = self.calendar.get_selected_date()
        
        # Добавляем минуты
        new_date = current_date + timedelta(minutes=minutes)
        
        # Обновляем календарь и спинбоксы
        self.calendar.selected_date = new_date
        self.calendar.current_date = new_date
        self.calendar._update_calendar()
        
        self.hours_var.set(new_date.strftime("%H"))
        self.minutes_var.set(new_date.strftime("%M"))
        self.reminder_data["due_date"] = new_date

    def _validate_fields(self) -> bool:
        """
        Проверить корректность заполненных полей.
        
        Returns:
            True, если все поля валидны
        """
        # Проверка заголовка
        title = self.title_entry.get().strip()
        if not title:
            messagebox.showwarning(
                "Ошибка валидации",
                "Заголовок обязателен для заполнения",
                parent=self.window
            )
            self.title_entry.focus()
            return False
        
        if len(title) > 200:
            messagebox.showwarning(
                "Ошибка валидации",
                "Заголовок не должен превышать 200 символов",
                parent=self.window
            )
            self.title_entry.focus()
            return False

        # Проверка даты и времени
        try:
            hours = int(self.hours_var.get())
            minutes = int(self.minutes_var.get())
            
            if not (0 <= hours <= 23):
                messagebox.showwarning(
                    "Ошибка валидации",
                    "Часы должны быть от 0 до 23",
                    parent=self.window
                )
                return False
            
            if not (0 <= minutes <= 59):
                messagebox.showwarning(
                    "Ошибка валидации",
                    "Минуты должны быть от 0 до 59",
                    parent=self.window
                )
                return False
            
            # Синхронизируем дату с календаря и временем
            selected_date = self.calendar.get_selected_date()
            combined_date = selected_date.replace(hour=hours, minute=minutes)
            
            # Проверка, что дата не в прошлом (с допуском 1 минута)
            if combined_date < datetime.now() - timedelta(minutes=1):
                if not messagebox.askyesno(
                    "Предупреждение",
                    "Выбранная дата уже прошла. Всё равно сохранить?",
                    parent=self.window
                ):
                    return False
            
            self.reminder_data["due_date"] = combined_date
            
        except ValueError:
            messagebox.showwarning(
                "Ошибка валидации",
                "Неверный формат времени",
                parent=self.window
            )
            return False
        
        return True

    def on_save(self):
        """
        Обработчик кнопки Сохранить.
        Сохраняет данные напоминания и закрывает диалог.
        """
        # Валидация полей
        if not self._validate_fields():
            return
        
        # Маппинг повторений
        repeat_map = {
            "Нет": None,
            "Час": "hour",
            "День": "day",
            "Неделя": "week",
            "Месяц": "month"
        }

        # Формирование результата
        self.result = {
            "title": self.title_entry.get().strip(),
            "description": self.description_text.get("1.0", tk.END).strip(),
            "due_date": self.reminder_data["due_date"],
            "repeat_interval": repeat_map[self.repeat_var.get()]
        }
        
        self.window.destroy()

    def on_cancel(self):
        """
        Обработчик кнопки Отмена.
        Закрывает диалог без сохранения.
        """
        self.window.destroy()