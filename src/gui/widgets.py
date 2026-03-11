"""Кастомные виджеты для GUI."""

import tkinter as tk
from tkinter import ttk
from calendar import monthcalendar
from datetime import datetime, date


class Calendar(ttk.Frame):
    """
    Виджет календаря для выбора даты.
    
    Пример использования:
        def on_date_selected(selected_date):
            print(f"Выбрано: {selected_date}")
        
        calendar = Calendar(parent, callback=on_date_selected)
        calendar.pack()
    """
    
    def __init__(self, parent, callback=None, selected_date=None, **kwargs):
        """
        Инициализация календаря.
        
        Args:
            parent: Родительский виджет
            callback: Функция обратного вызова при выборе даты (принимает datetime)
            selected_date: Изначально выбранная дата (datetime или None)
            **kwargs: Дополнительные аргументы для Frame
        """
        super().__init__(parent, **kwargs)
        self.callback = callback
        
        # Текущий месяц и год для отображения
        if selected_date:
            self.current_date = selected_date
        else:
            self.current_date = datetime.now()
        
        self.selected_date = selected_date
        
        self._setup_ui()
        self._update_calendar()
    
    def _setup_ui(self):
        """Настройка пользовательского интерфейса календаря."""
        # Заголовок с навигацией по месяцам
        header_frame = ttk.Frame(self)
        header_frame.pack(fill=tk.X, pady=3)
        
        self.prev_btn = ttk.Button(
            header_frame, 
            text="<", 
            command=self._prev_month,
            width=3
        )
        self.prev_btn.pack(side=tk.LEFT, padx=3)
        
        self.month_label = ttk.Label(header_frame, font=('Arial', 9, 'bold'))
        self.month_label.pack(side=tk.LEFT, expand=True)
        
        self.next_btn = ttk.Button(
            header_frame, 
            text=">", 
            command=self._next_month,
            width=3
        )
        self.next_btn.pack(side=tk.RIGHT, padx=3)
        
        # Дни недели
        days_frame = ttk.Frame(self)
        days_frame.pack(fill=tk.X, pady=2)
        
        days = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс']
        for day in days:
            ttk.Label(days_frame, text=day, width=4, font=('Arial', 8)).pack(side=tk.LEFT)
        
        # Сетка дней месяца
        self.days_frame = ttk.Frame(self)
        self.days_frame.pack(fill=tk.BOTH, expand=True, pady=2)
        
        # Кнопка выбора текущей даты
        today_btn = ttk.Button(
            self, 
            text="Сегодня", 
            command=self._select_today,
            width=12
        )
        today_btn.pack(pady=3)
    
    def _update_calendar(self):
        """Обновить отображение календаря для текущего месяца."""
        # Очистить сетку дней
        for widget in self.days_frame.winfo_children():
            widget.destroy()
        
        # Обновить заголовок с названием месяца и года
        month_names = [
            'Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь',
            'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь'
        ]
        self.month_label.config(
            text=f"{month_names[self.current_date.month - 1]} {self.current_date.year}"
        )
        
        # Получить календарь месяца
        cal_data = monthcalendar(
            self.current_date.year, 
            self.current_date.month
        )
        
        # Отобразить дни
        for week_num, week in enumerate(cal_data):
            for day_num, day in enumerate(week):
                if day == 0:
                    # Пустая ячейка (день не принадлежит этому месяцу)
                    ttk.Label(self.days_frame, text="", width=4).grid(
                        row=week_num, column=day_num
                    )
                else:
                    day_date = date(self.current_date.year, self.current_date.month, day)
                    is_today = day_date == date.today()
                    is_selected = (
                        self.selected_date and 
                        day_date == self.selected_date.date()
                    )
                    
                    # Стиль кнопки дня
                    style_name = "CalendarDay.TLabel" if not is_today else "CalendarToday.TLabel"
                    if is_selected:
                        style_name = "CalendarSelected.TLabel"
                    
                    btn = ttk.Button(
                        self.days_frame,
                        text=str(day),
                        width=4,
                        command=lambda d=day: self._on_day_selected(d)
                    )
                    
                    if is_today:
                        btn.config(style="Accent.TButton")
                    
                    btn.grid(row=week_num, column=day_num, padx=1, pady=1)
    
    def _prev_month(self):
        """Перейти к предыдущему месяцу."""
        if self.current_date.month == 1:
            self.current_date = self.current_date.replace(
                year=self.current_date.year - 1,
                month=12
            )
        else:
            self.current_date = self.current_date.replace(
                month=self.current_date.month - 1
            )
        self._update_calendar()
    
    def _next_month(self):
        """Перейти к следующему месяцу."""
        if self.current_date.month == 12:
            self.current_date = self.current_date.replace(
                year=self.current_date.year + 1,
                month=1
            )
        else:
            self.current_date = self.current_date.replace(
                month=self.current_date.month + 1
            )
        self._update_calendar()
    
    def _on_day_selected(self, day):
        """
        Обработчик выбора дня.
        
        Args:
            day: Выбранный день месяца
        """
        self.selected_date = datetime(
            self.current_date.year,
            self.current_date.month,
            day
        )
        self._update_calendar()
        
        if self.callback:
            self.callback(self.selected_date)
    
    def _select_today(self):
        """Выбрать сегодняшнюю дату."""
        self.selected_date = datetime.now()
        self.current_date = self.selected_date
        self._update_calendar()
        
        if self.callback:
            self.callback(self.selected_date)
    
    def get_selected_date(self) -> datetime:
        """
        Получить выбранную дату.
        
        Returns:
            Выбранная дата или текущая дата, если ничего не выбрано
        """
        return self.selected_date or datetime.now()
