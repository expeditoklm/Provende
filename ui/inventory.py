import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from ttkbootstrap.dialogs import Messagebox
from .base import BasePage
from utils import kg_to_bag_repr, safe_float
from .dialogs import MovementDialog

class InventoryPage(BasePage):
    def on_show(self):
        self.build()
        self.refresh()

    def build(self):
        for w in self.winfo_children():
            w.destroy()

        header = ttk.Frame(self); header.pack(fill=X)
        ttk.Label(header, text="Inventaire (comptage et ajustements)", font="-size 14 -weight bold").pack(side=LEFT)
        ttk.Button(header, text="Ajustement rapide", bootstyle="warning", command=self.adjust_selected).pack(side=RIGHT)
 
        ttk.Separator(self).pack(fill=X, pady=10)

        self.q_var = ttk.StringVar()
        s = ttk.Frame(self); s.pack(fill=X)
        ttk.Entry(s, textvariable=self.q_var).pack(side=LEFT)
        ttk.Button(s, text="Rechercher", bootstyle="secondary", command=self.refresh).pack(side=LEFT, padx=6)

        cols = ("id","libelle","poids_sac","stock_kg","stock_aff","seuil")
        self.tree = ttk.Treeview(self, columns=cols, show="headings", height=22, bootstyle="warning")
        self.tree.pack(fill=BOTH, expand=YES, pady=10)

        headers = {
            "id":"ID","libelle":"Produit","poids_sac":"1 sac (kg)", "stock_kg":"Stock (kg)",
            "stock_aff":"Stock (sacs+kg)", "seuil":"Seuil (kg)"
        }
        for c in cols:
            self.tree.heading(c, text=headers[c])
            anchor = E if c in ("poids_sac","stock_kg","seuil") else W
            self.tree.column(c, width=120 if c!="libelle" else 260, anchor=anchor)

        # Footer - set target
        form = ttk.Labelframe(self, text="Ajuster au stock ciblé")
        form.pack(fill=X, pady=8)
        self.target_var = ttk.StringVar()
        self.unit_var = ttk.StringVar(value="kg")
        row = ttk.Frame(form); row.pack(fill=X, padx=10, pady=8)
        ttk.Label(row, text="Nouvelle quantité").pack(side=LEFT, padx=(0,6))
        ttk.Entry(row, textvariable=self.target_var, width=12).pack(side=LEFT)
        ttk.Combobox(row, values=["kg","sac"], textvariable=self.unit_var, state="readonly", width=7).pack(side=LEFT, padx=6)
        ttk.Button(row, text="Ajuster", bootstyle="warning", command=self.adjust_selected).pack(side=LEFT, padx=10)

    def refresh(self):
        for i in self.tree.get_children():
            self.tree.delete(i)

        items = self.app.db.list_products(self.q_var.get())
        for p in items:
            stock = self.app.db.stock_kg(p["id"], shop_id=1)
            self.tree.insert("", END, values=(
                p["id"], p["libelle"], f'{p["poids_sac_kg"]:.2f}', f'{stock:.2f}',
                kg_to_bag_repr(stock, p["poids_sac_kg"]), f'{p["seuil_kg"]:.2f}'
            ))

    def adjust_selected(self):
        sel = self.tree.focus()
        if not sel:
            Messagebox.show_warning("Sélectionne un produit.", "Info")
            return
        vals = self.tree.item(sel, "values")
        pid = int(vals[0])
        prod = self.app.db.get_product(pid)
        current = self.app.db.stock_kg(pid, shop_id=1)

        # if no target provided -> open MovementDialog ADJ
        if not self.target_var.get().strip():
            MovementDialog(self.app, product=prod, mtype="ADJ", on_saved=self.refresh)
            return

        target = safe_float(self.target_var.get())
        if self.unit_var.get() == "sac":
            target = target * float(prod["poids_sac_kg"])

        delta = target - current
        if abs(delta) < 1e-9:
            Messagebox.show_info("Déjà à la bonne quantité.", "Info")
            return

        note = f"Ajustement inventaire -> cible {target:.2f} kg (delta {delta:+.2f} kg)"
        self.app.db.add_movement(product_id=pid, shop_id=1, mtype="ADJ", qty_kg=delta, note=note)
        Messagebox.show_info("Ajustement enregistré.", "OK")
        self.target_var.set("")
        self.refresh()