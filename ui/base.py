import ttkbootstrap as ttk

class BasePage(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app

    def on_show(self):
        pass