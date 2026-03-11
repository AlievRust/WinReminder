"""Точка входа в приложение Reminder."""

from tkinter import Tk
from gui.main_window import MainWindow


def main():
    """Запуск приложения."""
    root = Tk()
    root.title("Reminder")
    root.geometry("900x600")
    
    app = MainWindow(root)
    root.mainloop()


if __name__ == "__main__":
    main()