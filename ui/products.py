import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from ttkbootstrap.dialogs import Messagebox
from .base import BasePage
from .dialogs import ProductDialog, MovementDialog
from utils import kg_to_bag_repr

class ProductsPage(BasePage):
    def on_show(self):
        """Construit et rafraîchit la page quand elle est affichée."""
        self.build()
        self.refresh()

    def build(self):
        """Construit l'interface de la page des produits."""
        # Nettoie les widgets existants
        for w in self.winfo_children():
            w.destroy()

        header = ttk.Frame(self)
        header.pack(fill=X)
        ttk.Label(header, text="Produits", font="-size 14 -weight bold").pack(side=LEFT)

        # Bouton "Nouveau" dont l'état dépend du rôle de l'utilisateur
        if self.app.role == "a":
            ttk.Button(header, text="Nouveau", bootstyle="success", command=self.new_product).pack(side=RIGHT)
        else:
            # Désactive le bouton si le rôle est 'secretaire'
            ttk.Button(header, text="Nouveau", bootstyle="success", state="disabled").pack(side=RIGHT)

        ttk.Separator(self).pack(fill=X, pady=10)

        # Section de recherche
        search = ttk.Frame(self)
        search.pack(fill=X)
        self.q_var = ttk.StringVar()
        ttk.Entry(search, textvariable=self.q_var).pack(side=LEFT, padx=(0, 6))
        ttk.Button(search, text="Rechercher", bootstyle="secondary", command=self.refresh).pack(side=LEFT)
        ttk.Button(search, text="Rafraîchir", bootstyle="info", command=self.reset_and_refresh).pack(side=LEFT, padx=6)

        # Table des produits
        cols = ("id","sku","libelle","poids_sac","stock","prix_kg","prix_sac","seuil","actif")
        self.tree = ttk.Treeview(self, columns=cols, show="headings", height=20, bootstyle="primary")
        self.tree.pack(fill=BOTH, expand=YES, pady=10)

        for cid, label, w in [
            ("id","ID",60), ("sku","SKU",120), ("libelle","Libellé",260), ("poids_sac","1 sac (kg)",90),
            ("stock","Stock",160), ("prix_kg","Prix/kg",90), ("prix_sac","Prix/sac",90), ("seuil","Seuil(kg)",100), ("actif","Actif",60)
        ]:
            self.tree.heading(cid, text=label)
            self.tree.column(cid, width=w, anchor=(E if cid in ("poids_sac","prix_kg","prix_sac","seuil") else W))

        # Actions
        actions = ttk.Frame(self)
        actions.pack(fill=X)
        # Les boutons 'Modifier' et autres sont actifs pour les deux rôles, car la page les gère déjà.
        ttk.Button(actions, text="Modifier", bootstyle="secondary", command=self.edit_selected).pack(side=LEFT, padx=5)
        ttk.Button(actions, text="Archiver", bootstyle="danger", state="disabled", command=self.archive_selected).pack(side=LEFT, padx=5)
        ttk.Separator(actions, orient=VERTICAL).pack(side=LEFT, fill=Y, padx=10)
        ttk.Button(actions, text="Entrée (IN)", bootstyle="success", command=lambda: self.move_selected("IN")).pack(side=LEFT, padx=5)
        ttk.Button(actions, text="Sortie (OUT)", bootstyle="danger", command=lambda: self.move_selected("OUT")).pack(side=LEFT, padx=5)
        ttk.Button(actions, text="Ajustement (ADJ)", bootstyle="warning", command=lambda: self.move_selected("ADJ")).pack(side=LEFT, padx=5)

        # Lier le double-clic pour l'édition
        self.tree.bind("<Double-1>", lambda e: self.edit_selected())

    def refresh(self):
        """Met à jour les données affichées dans la table."""
        for i in self.tree.get_children():
            self.tree.delete(i)

        items = self.app.db.list_products(self.q_var.get())
        for p in items:
            stock = self.app.db.stock_kg(p["id"], shop_id=1)
            stock_aff = kg_to_bag_repr(stock, p["poids_sac_kg"])
            self.tree.insert("", END, values=(
                p["id"], p.get("sku",""), p["libelle"], f'{p["poids_sac_kg"]:.2f}',
                stock_aff, f'{p["prix_kg"]:.0f}', f'{p["prix_sac"]:.0f}', f'{p["seuil_kg"]:.0f}', "Oui" if p.get("actif",1) else "Non"
            ))

    
    def reset_and_refresh(self):
        """
        Vide le champ de recherche et rafraîchit la liste des produits.
        """
        self.q_var.set("")
        self.refresh()

    def selected_product(self):
        """Retourne le dictionnaire du produit sélectionné, ou None si aucun n'est sélectionné."""
        sel = self.tree.focus()
        if not sel:
            Messagebox.show_warning("Sélectionne un produit.", "Info")
            return None
        pid = int(self.tree.item(sel, "values")[0])
        return self.app.db.get_product(pid)

    def new_product(self):
        """Ouvre une boîte de dialogue pour créer un nouveau produit."""
        ProductDialog(self.app, on_saved=self.refresh)

    def edit_selected(self):
        """Ouvre une boîte de dialogue pour modifier le produit sélectionné."""
        p = self.selected_product()
        if p:
            ProductDialog(self.app, product=p, on_saved=self.refresh)

    def archive_selected(self):
        """Archive le produit sélectionné."""
        p = self.selected_product()
        if not p: return
        if Messagebox.okcancel("Archiver ce produit ? Il n'apparaîtra plus dans les listes actives.", "Confirmer"):
            self.app.db.archive_product(p["id"])
            self.refresh()

    def move_selected(self, mtype: str):
        """Ouvre une boîte de dialogue pour créer un mouvement de stock pour le produit sélectionné."""
        p = self.selected_product()
        if not p: return
        MovementDialog(self.app, product=p, mtype=mtype, on_saved=self.refresh)
