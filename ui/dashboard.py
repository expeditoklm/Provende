import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from .base import BasePage

# Dans la classe DashboardPage
class DashboardPage(BasePage):
    def on_show(self):
        self.build()

    def build(self):
        for w in self.winfo_children():
            w.destroy()

        cards = ttk.Frame(self)
        cards.pack(fill=X)
        metrics = [
            ("Stock total (kg)", f"{self.app.db.total_stock_kg(1):.2f}", "primary"),
            ("Nombre de produits", str(len(self.app.db.list_products())), "success"),
            ("Boutiques", str(len(self.app.db.list_shops())), "info"),
        ]
        for title, value, style in metrics:
            f = ttk.Frame(cards, padding=15, bootstyle=style)
            f.pack(side=LEFT, padx=10, pady=10, fill=X, expand=YES)
            # Utilise le nouveau style pour les étiquettes
            ttk.Label(f, text=title, font="-size 12 -weight bold", style="Card.TLabel").pack(anchor=W)
            ttk.Label(f, text=value, font="-size 16 -weight bold", style="Card.TLabel").pack(anchor=W)