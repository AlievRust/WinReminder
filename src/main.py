"""Точка входа в приложение Reminder."""

import tkinter as tk
from tkinter import messagebox

from core.service import ReminderService
from gui.main_window import MainWindow


def main():
    """Запуск приложения."""
    # Создаём сервис напоминаний
    reminder_service = ReminderService()
    
    # Создаём главное окно Tkinter
    root = tk.Tk()
    root.title("Reminder")
    root.geometry("900x600")
    
    # Обработка закрытия приложения
    def on_closing():
        """Обработчик закрытия приложения."""
        try:
            reminder_service.stop()
        except Exception as e:
            print(f"Ошибка при остановке сервиса: {e}")
        root.destroy()
    
    root.protocol("WM_DELETE_WINDOW", on_closing)
    
    # Создаём главное окно приложения с сервисом
    app = MainWindow(root, reminder_service)
    
    # Запускаем сервис напоминаний
    try:
        reminder_service.start()
    except Exception as e:
        messagebox.showerror(
            "Ошибка запуска",
            f"Не удалось запустить сервис напоминаний: {e}"
        )
    
    # Запускаем главный цикл Tkinter
    root.mainloop()


if __name__ == "__main__":
    main()