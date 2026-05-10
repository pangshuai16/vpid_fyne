import sys
import os


def get_base_path():
    if getattr(sys, 'frozen', False):
        return sys._MEIPASS
    return os.path.dirname(os.path.abspath(__file__))


sys.path.insert(0, get_base_path())


def main():
    try:
        from src.gui.main_window import MainWindow
        app = MainWindow()
        app.run()
    except Exception as e:
        import traceback
        import tkinter as tk
        from tkinter import messagebox
        if tk._default_root is None:
            root = tk.Tk()
            root.withdraw()
        error_msg = "{0}\n\n{1}".format(str(e), traceback.format_exc())
        messagebox.showerror("Fatal Error", error_msg)
        if tk._default_root:
            tk._default_root.destroy()


if __name__ == "__main__":
    main()
