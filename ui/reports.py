import csv
import os
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from ttkbootstrap.dialogs import Messagebox
from tkinter import filedialog
from .base import BasePage
from utils import kg_to_bag_repr

class ReportsPage(BasePage):
    def on_show(self):
        self.build()
        self.refresh()

    def build(self):
        for w in self.winfo_children():
            w.destroy()

        header = ttk.Frame(self); header.pack(fill=X)
        ttk.Label(header, text="Rapports", font="-size 14 -weight bold").pack(side=LEFT)
        ttk.Button(header, text="Exporter CSV (stocks)", bootstyle="secondary", command=self.export_csv).pack(side=RIGHT)

        ttk.Separator(self).pack(fill=X, pady=10)

        # Low stock
        ttk.Label(self, text="Ruptures / Sous seuil", font="-size 12 -weight bold").pack(anchor=W)

        cols = ("id","libelle","stock_kg","stock_aff","seuil","poids_sac")
        self.tree = ttk.Treeview(self, columns=cols, show="headings", height=18, bootstyle="success")
        self.tree.pack(fill=BOTH, expand=YES, pady=8)

        headers = {
            "id":"ID","libelle":"Produit","stock_kg":"Stock (kg)","stock_aff":"Stock (sacs+kg)","seuil":"Seuil (kg)","poids_sac":"1 sac (kg)"
        }
        for c in cols:
            self.tree.heading(c, text=headers[c])
            anchor = E if c in ("stock_kg","seuil","poids_sac") else W
            self.tree.column(c, width=130 if c!="libelle" else 260, anchor=anchor)

    def refresh(self):
        for i in self.tree.get_children():
            self.tree.delete(i)

        items = self.app.db.low_stock_products(shop_id=1)
        for p in items:
            self.tree.insert("", END, values=(
                p["id"], p["libelle"], f'{p["stock_kg"]:.2f}',
                kg_to_bag_repr(p["stock_kg"], p["poids_sac_kg"]),
                f'{p["seuil_kg"]:.2f}', f'{p["poids_sac_kg"]:.2f}'
            ))

    def export_csv(self):
        path = filedialog.asksaveasfilename(
            title="Exporter les stocks",
            defaultextension=".csv",
            filetypes=[("CSV", "*.csv")],
            initialfile="stocks.csv"
        )
        if not path:
            return
        try:
            with open(path, "w", newline="", encoding="utf-8") as f:
                w = csv.writer(f, delimiter=";")
                w.writerow(["ID","Produit","Stock (kg)","Stock (sacs+kg)","Seuil (kg)","1 sac (kg)"])
                items = self.app.db.all_stocks(shop_id=1)
                for p, qty in items:
                    w.writerow([
                        p["id"], p["libelle"], f"{qty:.2f}",
                        kg_to_bag_repr(qty, p["poids_sac_kg"]),
                        f'{p["seuil_kg"]:.2f}', f'{p["poids_sac_kg"]:.2f}'
                    ])
            Messagebox.show_info("Export terminé.", "OK")
        except Exception as e:
            Messagebox.show_error(str(e), "Erreur")