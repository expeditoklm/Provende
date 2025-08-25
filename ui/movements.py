import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from ttkbootstrap.dialogs import Messagebox
from ttkbootstrap import DateEntry  # Import direct de DateEntry
from .base import BasePage
from .dialogs import MovementDialog
from utils import kg_to_bag_repr

class MovementsPage(BasePage):
    def on_show(self):
        self.build()
        self.refresh()

    def build(self):
        for w in self.winfo_children():
            w.destroy()

        header = ttk.Frame(self); header.pack(fill=X)
        ttk.Label(header, text="Mouvements (Entrées / Sorties / Ajustements)", font="-size 14 -weight bold").pack(side=LEFT)
        ttk.Button(header, text="Nouveau mouvement", bootstyle="success", command=self.new_movement).pack(side=RIGHT)

        ttk.Separator(self).pack(fill=X, pady=10)

        # Filters
        f = ttk.Frame(self); f.pack(fill=X)
        self.q_var = ttk.StringVar()
        self.type_var = ttk.StringVar(value="Tous")
        self.shop_var = ttk.StringVar(value="Toutes")
        
        shops = self.app.db.list_shops()
        shop_names = ["Toutes"] + [s["libelle"] for s in shops]
        ttk.Label(f, text="Recherche").pack(side=LEFT, padx=(0,6))
        ttk.Entry(f, textvariable=self.q_var, width=20).pack(side=LEFT)
        ttk.Label(f, text="Type").pack(side=LEFT, padx=(10,6))
        ttk.Combobox(f, values=["Tous","IN","OUT","ADJ"], textvariable=self.type_var, width=8, state="readonly").pack(side=LEFT)
        ttk.Label(f, text="Boutique").pack(side=LEFT, padx=(10,6))
        ttk.Combobox(f, values=shop_names, textvariable=self.shop_var, width=25, state="readonly").pack(side=LEFT)
        
        ttk.Label(f, text="Du").pack(side=LEFT, padx=(10,6))
        self.date_from_entry = DateEntry(f, width=12, dateformat="%Y-%m-%d", bootstyle="primary")
        self.date_from_entry.pack(side=LEFT)

        ttk.Label(f, text="Au").pack(side=LEFT, padx=(6,6))
        self.date_to_entry = DateEntry(f, width=12, dateformat="%Y-%m-%d", bootstyle="primary")
        self.date_to_entry.pack(side=LEFT)
        
        ttk.Button(f, text="Filtrer", bootstyle="secondary", command=self.refresh).pack(side=LEFT, padx=8)
        ttk.Button(f, text="Rafraîchir", bootstyle="info", command=self.refresh).pack(side=LEFT)

        # ---
        # Summary Frame (newly added)
        # ---
        summary_frame = ttk.Frame(self)
        summary_frame.pack(fill=X, pady=(10, 0))

        # Labels to display summary values
        self.total_in_var = ttk.StringVar(value="Valeur des entrées : 0.00 FCFA")
        self.total_out_var = ttk.StringVar(value="Valeur des sorties : 0.00 FCFA")
        self.profit_var = ttk.StringVar(value="Bénéfice net : 0.00 FCFA")

        ttk.Label(summary_frame, textvariable=self.total_in_var, font="-size 10 -weight bold", bootstyle="success").pack(side=LEFT, padx=(0, 20))
        ttk.Label(summary_frame, textvariable=self.total_out_var, font="-size 10 -weight bold", bootstyle="danger").pack(side=LEFT, padx=(0, 20))
        self.profit_label = ttk.Label(summary_frame, textvariable=self.profit_var, font="-size 12 -weight bold")
        self.profit_label.pack(side=LEFT)

        ttk.Separator(self).pack(fill=X, pady=10)

        # Table
        cols = ("date","type","produit","boutique","quantite","en_sacs","prix_unit","note")
        self.tree = ttk.Treeview(self, columns=cols, show="headings", height=22, bootstyle="info")
        self.tree.pack(fill=BOTH, expand=YES, pady=10)

        headers = {
            "date":"Date", "type":"Type", "produit":"Produit", "boutique":"Boutique",
            "quantite":"Qté (kg)", "en_sacs":"Qté (sacs+kg)", "prix_unit":"Prix/kg", "note":"Note"
        }
        for c in cols:
            self.tree.heading(c, text=headers[c])
            anchor = E if c in ("quantite","prix_unit") else W
            self.tree.column(c, width=120 if c not in ("note","produit") else 220, anchor=anchor)

    def refresh(self):
        for i in self.tree.get_children():
            self.tree.delete(i)

        mtype = self.type_var.get()
        mt = None if mtype == "Tous" else mtype

        shop_name = self.shop_var.get()
        shops = self.app.db.list_shops()
        shop_id = None
        if shop_name and shop_name != "Toutes":
            for s in shops:
                if s["libelle"] == shop_name:
                    shop_id = s["id"]
                    break

        # Récupère les dates au format YYYY-MM-DD depuis le DateEntry
        date_from = self.date_from_entry.entry.get().strip() or None
        date_to = self.date_to_entry.entry.get().strip() or None

        items = self.app.db.list_movements(
            mtype=mt,
            shop_id=shop_id,
            q=self.q_var.get(),
            date_from=date_from,
            date_to=date_to
        )

        # ---
        # Calculate summary totals (newly added)
        # ---
        total_in_value = 0
        total_out_value = 0
        for m in items:
            if m["type"] == "IN":
                total_in_value += m["qty_kg"] * m["unit_price_kg"]
            elif m["type"] == "OUT":
                # Use absolute value for OUT movements
                total_out_value += abs(m["qty_kg"]) * m["unit_price_kg"]
        
        profit = total_out_value - total_in_value
        
        # Update summary labels
        self.total_in_var.set(f"Valeur des entrées : {total_in_value:,.2f} FCFA")
        self.total_out_var.set(f"Valeur des sorties : {total_out_value:,.2f} FCFA")
        self.profit_var.set(f"Bénéfice net : {profit:,.2f} FCFA")
        
        # Change color based on profit/loss
        if profit >= 0:
            self.profit_label.config(bootstyle="success")
        else:
            self.profit_label.config(bootstyle="danger")

        # Populate the Treeview
        for m in items:
            sacs_repr = kg_to_bag_repr(abs(m["qty_kg"]), m["poids_sac_kg"])
            self.tree.insert("", END, values=(
                m["created_at"], m["type"], m["product_libelle"], m["shop_libelle"],
                f'{m["qty_kg"]:.2f}', sacs_repr, f'{(m["unit_price_kg"] or 0):.0f}', m.get("note","")
            ))

    def new_movement(self):
        MovementDialog(self.app, on_saved=self.refresh)