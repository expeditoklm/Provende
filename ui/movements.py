import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from ttkbootstrap.dialogs import Messagebox
from ttkbootstrap import DateEntry 
from .base import BasePage
from .dialogs import MovementDialog
from utils import kg_to_bag_repr







class MovementsPage(BasePage):
    """
    Page pour afficher et gérer les mouvements (entrées, sorties, ajustements) des produits.
    Cette version a été mise à jour pour inclure la colonne 'cout' et une section de résumé.
    """
    def on_show(self):
        """
        Méthode appelée lors de l'affichage de la page.
        Construit l'interface utilisateur et rafraîchit les données.
        """
        self.build()
        self.refresh()

    def build(self):
        """
        Construit l'interface utilisateur de la page des mouvements.
        Détruit tous les widgets existants avant de les reconstruire.
        """
        # Détruit tous les widgets existants pour reconstruire l'interface
        for w in self.winfo_children():
            w.destroy()

        # En-tête de la page
        header = ttk.Frame(self)
        header.pack(fill=X)
        ttk.Label(header, text="Mouvements (Entrées / Sorties / Ajustements)", font="-size 14 -weight bold").pack(side=LEFT)
        ttk.Button(header, text="Nouveau mouvement", bootstyle="success", command=self.new_movement).pack(side=RIGHT)

        ttk.Separator(self).pack(fill=X, pady=10)

        # Cadre des filtres de recherche
        f = ttk.Frame(self)
        f.pack(fill=X)
        self.q_var = ttk.StringVar()
        self.type_var = ttk.StringVar(value="Tous")
        self.shop_var = ttk.StringVar(value="Toutes")
        
        shops = self.app.db.list_shops()
        shop_names = ["Toutes"] + [s["libelle"] for s in shops]
        
        ttk.Label(f, text="Recherche").pack(side=LEFT, padx=(0,6))
        ttk.Entry(f, textvariable=self.q_var, width=20).pack(side=LEFT)
        ttk.Label(f, text="Type").pack(side=LEFT, padx=(10,6))
        self.type_combo = ttk.Combobox(f, values=["Tous", "IN", "OUT", "ADJ"], textvariable=self.type_var, width=8, state="readonly")
        self.type_combo.pack(side=LEFT)
        
        ttk.Label(f, text="Boutique").pack(side=LEFT, padx=(10,6))
        self.shop_combo = ttk.Combobox(f, values=shop_names, textvariable=self.shop_var, width=25, state="readonly")
        self.shop_combo.pack(side=LEFT)
        
        ttk.Label(f, text="Du").pack(side=LEFT, padx=(10,6))
        self.date_from_entry = DateEntry(f, width=12, dateformat="%Y-%m-%d", bootstyle="primary")
        self.date_from_entry.pack(side=LEFT)

        ttk.Label(f, text="Au").pack(side=LEFT, padx=(6,6))
        self.date_to_entry = DateEntry(f, width=12, dateformat="%Y-%m-%d", bootstyle="primary")
        self.date_to_entry.pack(side=LEFT)
        
        ttk.Button(f, text="Filtrer", bootstyle="secondary", command=self.refresh).pack(side=LEFT, padx=8)
        ttk.Button(f, text="Rafraîchir", bootstyle="info", command=self.refresh).pack(side=LEFT)
        
        # Associer les événements de sélection aux combos
        self.type_combo.bind("<<ComboboxSelected>>", lambda e: self.refresh())
        self.shop_combo.bind("<<ComboboxSelected>>", lambda e: self.refresh())

        # Cadre de résumé pour afficher les totaux
        summary_frame = ttk.Frame(self)
        summary_frame.pack(fill=X, pady=(10, 0))

        # Variables pour les labels de résumé
        self.total_sales_var = ttk.StringVar(value="Valeur des ventes : 0.00 FCFA")
        self.total_cogs_var = ttk.StringVar(value="Coût des ventes : 0.00 FCFA")
        self.profit_var = ttk.StringVar(value="Bénéfice net : 0.00 FCFA")

        ttk.Label(summary_frame, textvariable=self.total_sales_var, font="-size 10 -weight bold", bootstyle="success").pack(side=LEFT, padx=(0, 20))
        ttk.Label(summary_frame, textvariable=self.total_cogs_var, font="-size 10 -weight bold", bootstyle="danger").pack(side=LEFT, padx=(0, 20))
        self.profit_label = ttk.Label(summary_frame, textvariable=self.profit_var, font="-size 12 -weight bold")
        self.profit_label.pack(side=LEFT)

        ttk.Separator(self).pack(fill=X, pady=10)

        # Tableau (Treeview) pour afficher la liste des mouvements
        cols = ("date", "type", "produit", "boutique", "quantite", "en_sacs", "prix_unit_kg", "prix_sac", "cout", "note")
        self.tree = ttk.Treeview(self, columns=cols, show="headings", height=22, bootstyle="info")
        self.tree.pack(fill=BOTH, expand=YES, pady=10)

        # En-têtes et propriétés des colonnes
        headers = {
            "date": "Date", "type": "Type", "produit": "Produit", "boutique": "Boutique",
            "quantite": "Qté (kg)", "en_sacs": "Qté (sacs+kg)", "prix_unit_kg": "Prix/kg",
            "prix_sac": "Prix/sac", "cout": "Coût", "note": "Note"
        }
        for c in cols:
            self.tree.heading(c, text=headers[c])
            anchor = E if c in ("quantite", "prix_unit_kg", "prix_sac", "cout") else W
            self.tree.column(c, width=120 if c not in ("note", "produit") else 220, anchor=anchor)

    def refresh(self):
        """
        Récupère les données de la base de données et rafraîchit le tableau et les valeurs de résumé.
        """
        # Efface les données existantes du tableau
        for i in self.tree.get_children():
            self.tree.delete(i)

        # Récupère les paramètres de filtre
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

        date_from = self.date_from_entry.entry.get().strip() or None
        date_to = self.date_to_entry.entry.get().strip() or None

        # Appelle la base de données pour obtenir les mouvements filtrés
        items = self.app.db.list_movements(
            mtype=mt,
            shop_id=shop_id,
            q=self.q_var.get(),
            date_from=date_from,
            date_to=date_to
        )
        
        # Calcule les totaux en utilisant la nouvelle fonction de la DB
        total_sales_value, total_cogs_value = self.app.db.total_sales_and_cogs(
            mtype=mt,
            shop_id=shop_id,
            q=self.q_var.get(),
            date_from=date_from,
            date_to=date_to
        )
        
        profit = total_sales_value - total_cogs_value
        
        # Met à jour les labels de résumé
        self.total_sales_var.set(f"Valeur des ventes : {total_sales_value:,.2f} FCFA")
        self.total_cogs_var.set(f"Coût des ventes : {total_cogs_value:,.2f} FCFA")
        self.profit_var.set(f"Bénéfice net : {profit:,.2f} FCFA")
        
        # Change la couleur du label de bénéfice selon le résultat
        if profit >= 0:
            self.profit_label.config(bootstyle="success")
        else:
            self.profit_label.config(bootstyle="danger")

        # Remplit le tableau avec les données des mouvements
        for m in items:
            sacs_repr = kg_to_bag_repr(abs(m["qty_kg"]), m.get("poids_sac_kg", 0))
            self.tree.insert("", END, values=(
                m["created_at"],
                m["type"],
                m["product_libelle"],
                m["shop_libelle"],
                f'{m["qty_kg"]:.2f}',
                sacs_repr,
                f'{(m["unit_price_kg"] or 0):.0f}',
                f'{(m["unit_price_sac"] or 0):.0f}',
                f'{(m["cost"] or 0):,.2f}',
                m.get("note", "")
            ))

    # --- NOUVELLE MÉTHODE AJOUTÉE ---
    def new_movement(self):
        """
        Ouvre la boîte de dialogue pour créer un nouveau mouvement.
        """
        MovementDialog(self.app, on_saved=self.refresh)
