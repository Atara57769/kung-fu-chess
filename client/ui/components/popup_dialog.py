import tkinter as tk
from tkinter import messagebox

TK_TOPMOST_ATTR = "-topmost"

def show_error_dialog(title: str, message: str) -> None:
    """Displays a native OS error popup message box."""
    root = tk.Tk()
    root.withdraw()
    root.attributes(TK_TOPMOST_ATTR, True)
    messagebox.showerror(title, message, parent=root)
    root.destroy()

def show_warning_dialog(title: str, message: str) -> None:
    """Displays a native OS warning popup message box."""
    root = tk.Tk()
    root.withdraw()
    root.attributes(TK_TOPMOST_ATTR, True)
    messagebox.showwarning(title, message, parent=root)
    root.destroy()

def show_info_dialog(title: str, message: str) -> None:
    """Displays a native OS information popup message box."""
    root = tk.Tk()
    root.withdraw()
    root.attributes(TK_TOPMOST_ATTR, True)
    messagebox.showinfo(title, message, parent=root)
    root.destroy()

