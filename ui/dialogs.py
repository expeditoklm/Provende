import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from ttkbootstrap.dialogs import QueryDialog ,Messagebox
from utils import safe_float
from ttkbootstrap import DateEntry  # Correction de l'importation

class ProductDialog:
    def __init__(self, app, product=None, on_saved=None):
        self.app = app
        self.product = product
        self.on_saved = on_saved

        self.win = ttk.Toplevel(title="Modifier produit" if product else "Nouveau produit", resizable=(False, False))
        self.win.transient(app)
        self.win.grab_set()

        frm = ttk.Frame(self.win, padding=15)
        frm.pack(fill=BOTH, expand=YES)

        self.vars = {}
        rows = [
            ("SKU (optionnel)", "sku", product.get("sku") if product else ""),
            ("Libellé", "libelle", product.get("libelle") if product else ""),
            ("Poids d'un sac (kg)", "poids_sac_kg", str(product.get("poids_sac_kg")) if product else "50"),
            ("Prix au kg", "prix_kg", str(product.get("prix_kg")) if product else "0"),
            ("Prix au sac", "prix_sac", str(product.get("prix_sac")) if product else "0"),
            ("Seuil alerte (kg)", "seuil_kg", str(product.get("seuil_kg")) if product else "0"),
        ]
        for label, key, init in rows:
            r = ttk.Frame(frm); r.pack(fill=X, pady=6)
            ttk.Label(r, text=label, width=20).pack(side=LEFT)
            var = ttk.StringVar(value=init)
            self.vars[key] = var
            ttk.Entry(r, textvariable=var).pack(side=LEFT, fill=X, expand=YES)

        ttk.Separator(frm).pack(fill=X, pady=10)
        btns = ttk.Frame(frm); btns.pack(fill=X)
        ttk.Button(btns, text="Annuler", bootstyle="secondary", command=self.win.destroy).pack(side=RIGHT, padx=5)
        ttk.Button(btns, text="Enregistrer", bootstyle="success", command=self.save).pack(side=RIGHT)

    def save(self):
        data = {k: v.get().strip() for k, v in self.vars.items()}
        if not data["libelle"]:
            Messagebox.show_error("Le libellé est obligatoire.", "Erreur")
            return
        try:
            if self.product:
                self.app.db.update_product(
                    pid=self.product["id"],
                    sku=data["sku"] or None,
                    libelle=data["libelle"],
                    poids_sac_kg=safe_float(data["poids_sac_kg"]),
                    prix_kg=safe_float(data["prix_kg"]),
                    prix_sac=safe_float(data["prix_sac"]),
                    seuil_kg=safe_float(data["seuil_kg"]),
                    actif=self.product.get("actif", 1)
                )
            else:
                self.app.db.add_product(
                    sku=data["sku"] or None,
                    libelle=data["libelle"],
                    poids_sac_kg=safe_float(data["poids_sac_kg"]),
                    prix_kg=safe_float(data["prix_kg"]),
                    prix_sac=safe_float(data["prix_sac"]),
                    seuil_kg=safe_float(data["seuil_kg"])
                )
            if callable(self.on_saved):
                self.on_saved()
            self.win.destroy()
        except Exception as e:
            Messagebox.show_error(str(e), "Erreur")





class MovementDialog(ttk.Toplevel):
    """
    Boîte de dialogue pour créer ou modifier un mouvement de stock.
    """
    def __init__(self, parent, product=None, mtype=None, on_saved=None):
        super().__init__(parent)
        self.transient(parent)
        self.grab_set()
        self.app = parent
        self.on_saved = on_saved
        self.product = product
        self.mtype = mtype
        self.result = None
        
        if not hasattr(self.app.db, 'get_shop_by_libelle'):
            self.app.db.get_shop_by_libelle = lambda libelle: next((s for s in self.app.db.list_shops() if s["libelle"] == libelle), None)
        
        if not hasattr(self.app.db, 'get_product_by_libelle'):
            self.app.db.get_product_by_libelle = lambda libelle: next((p for p in self.app.db.list_products() if p["libelle"] == libelle), None)
            
        self.default_shop = self.app.db.list_shops()[0]

        title_suffix = {
            "IN": "Entrée",
            "OUT": "Sortie",
            "ADJ": "Ajustement"
        }.get(mtype, "Mouvement")
        self.title(f"Nouveau mouvement ({title_suffix})")
        
        self.main_frame = ttk.Frame(self, padding=20)
        self.main_frame.pack(fill=BOTH, expand=YES)
        
        ttk.Label(self.main_frame, text=f"Mouvement de stock ({title_suffix})", font="-size 12 -weight bold").pack(pady=(0, 10))
        
        # Variables de données
        self.date_var = ttk.StringVar()
        self.shop_var = ttk.StringVar(value=self.default_shop["libelle"])
        self.product_var = ttk.StringVar(value=self.product["libelle"] if self.product else "")
        self.poids_sac_var = ttk.DoubleVar()
        self.prix_sac_var = ttk.DoubleVar()
        self.qty_kg_saisie_var = ttk.DoubleVar() 
        self.qty_sac_saisie_var = ttk.DoubleVar() 
        self.price_kg_var = ttk.DoubleVar()
        self.note_var = ttk.StringVar()
        
        if self.product:
            if self.product.get("prix_kg") is not None:
                self.price_kg_var.set(self.product["prix_kg"])
            else:
                self.price_kg_var.set(0)
            
            if self.product.get("poids_sac_kg") is not None:
                self.poids_sac_var.set(self.product["poids_sac_kg"])
            else:
                self.poids_sac_var.set(0)
            
            if self.product.get("prix_sac") is not None:
                self.prix_sac_var.set(self.product["prix_sac"])
            else:
                self.prix_sac_var.set(0)

        # Création des widgets
        f = ttk.Frame(self.main_frame)
        f.pack(fill=X, pady=5)
        ttk.Label(f, text="Date:", width=15).pack(side=LEFT)
        self.date_entry = DateEntry(f, dateformat="%Y-%m-%d", bootstyle="primary")
        self.date_entry.pack(side=LEFT, fill=X, expand=YES)

        f = ttk.Frame(self.main_frame)
        f.pack(fill=X, pady=5)
        ttk.Label(f, text="Boutique:", width=15).pack(side=LEFT)
        shops = self.app.db.list_shops()
        shop_names = [s["libelle"] for s in shops]
        self.shop_combo = ttk.Combobox(f, values=shop_names, textvariable=self.shop_var, state="readonly")
        self.shop_combo.pack(side=LEFT, fill=X, expand=YES)
        self.shop_combo.current(shop_names.index(self.default_shop["libelle"]))

        f = ttk.Frame(self.main_frame)
        f.pack(fill=X, pady=5)
        ttk.Label(f, text="Produit:", width=15).pack(side=LEFT)
        self.product_combo = ttk.Combobox(f, textvariable=self.product_var, state="readonly")
        self.product_combo.pack(side=LEFT, fill=X, expand=YES)
        if not self.product:
            self.product_combo["values"] = [p["libelle"] for p in self.app.db.list_products(include_inactive=False)]
        else:
            self.product_combo["values"] = [self.product["libelle"]]
        self.product_combo.bind("<<ComboboxSelected>>", self.on_product_select)

        # Champs pour la quantité en sacs
        f = ttk.Frame(self.main_frame)
        f.pack(fill=X, pady=5)
        ttk.Label(f, text="Quantité (sacs):", width=15).pack(side=LEFT)
        self.qty_sac_entry = ttk.Entry(f, textvariable=self.qty_sac_saisie_var)
        self.qty_sac_entry.pack(side=LEFT, fill=X, expand=YES)

        # Champs pour la quantité en kg
        f = ttk.Frame(self.main_frame)
        f.pack(fill=X, pady=5)
        ttk.Label(f, text="Quantité (kg):", width=15).pack(side=LEFT)
        self.qty_kg_entry = ttk.Entry(f, textvariable=self.qty_kg_saisie_var)
        self.qty_kg_entry.pack(side=LEFT, fill=X, expand=YES)
        
        f = ttk.Frame(self.main_frame)
        f.pack(fill=X, pady=5)
        ttk.Label(f, text="Prix/kg (FCFA):", width=15).pack(side=LEFT)
        self.price_entry = ttk.Entry(f, textvariable=self.price_kg_var)
        self.price_entry.pack(side=LEFT, fill=X, expand=YES)

        f = ttk.Frame(self.main_frame)
        f.pack(fill=X, pady=5)
        ttk.Label(f, text="Prix/sac (FCFA):", width=15).pack(side=LEFT)
        self.price_sac_entry = ttk.Entry(f, textvariable=self.prix_sac_var)
        self.price_sac_entry.pack(side=LEFT, fill=X, expand=YES)

        f = ttk.Frame(self.main_frame)
        f.pack(fill=X, pady=5)
        ttk.Label(f, text="Note:", width=15).pack(side=LEFT)
        self.note_entry = ttk.Entry(f, textvariable=self.note_var)
        self.note_entry.pack(side=LEFT, fill=X, expand=YES)

        # Boutons
        button_frame = ttk.Frame(self.main_frame)
        button_frame.pack(fill=X, pady=(10, 0))
        ttk.Button(button_frame, text="Annuler", command=self.destroy).pack(side=RIGHT)
        ttk.Button(button_frame, text="Enregistrer", bootstyle="success", command=self.save).pack(side=RIGHT, padx=5)
        
        self.update_idletasks()
        x = parent.winfo_x() + parent.winfo_width() // 2 - self.winfo_width() // 2
        y = parent.winfo_y() + parent.winfo_height() // 2 - self.winfo_height() // 2
        self.geometry(f"+{x}+{y}")

    def on_product_select(self, event=None):
        product_libelle = self.product_var.get()
        if product_libelle:
            product = self.app.db.get_product_by_libelle(product_libelle)
            if product:
                if product.get("prix_kg") is not None:
                    self.price_kg_var.set(product["prix_kg"])
                else:
                    self.price_kg_var.set(0)
                
                if product.get("poids_sac_kg") is not None:
                    self.poids_sac_var.set(product["poids_sac_kg"])
                else:
                    self.poids_sac_var.set(0)
                
                if product.get("prix_sac") is not None:
                    self.prix_sac_var.set(product["prix_sac"])
                else:
                    self.prix_sac_var.set(0)
            else:
                self.price_kg_var.set(0)
                self.poids_sac_var.set(0)
                self.prix_sac_var.set(0)

    def save(self):
        try:
            # Récupération des données du formulaire
            shop = self.app.db.get_shop_by_libelle(self.shop_var.get())
            if not shop:
                Messagebox.show_warning("Boutique non trouvée.", "Erreur")
                return

            product_libelle = self.product_var.get()
            product = self.app.db.get_product_by_libelle(product_libelle)
            if not product:
                Messagebox.show_warning("Produit non trouvé.", "Erreur")
                return

            qty_sac = self.qty_sac_saisie_var.get()
            qty_kg_saisie = self.qty_kg_saisie_var.get()
            poids_sac = self.poids_sac_var.get()

            if poids_sac == 0:
                Messagebox.show_warning("Le poids du sac pour ce produit est de 0. Veuillez le mettre à jour dans la liste des produits.", "Erreur")
                return
            
            if qty_sac == 0 and qty_kg_saisie == 0:
                Messagebox.show_warning("Veuillez saisir une quantité en kg ou en sacs.", "Erreur")
                return
            
            # Calcul de la quantité totale en kg
            total_qty_kg = (qty_sac * poids_sac) + qty_kg_saisie
            
            if self.mtype in ("OUT", "ADJ"):
                total_qty_kg = -abs(total_qty_kg) # Utilisez la valeur absolue pour les sorties
            if self.mtype == "ADJ":
                current_stock = self.app.db.stock_kg(product["id"], shop["id"])
                total_qty_kg = total_qty_kg - current_stock

            price_kg = self.price_kg_var.get()
            note = self.note_var.get()

            # Enregistrement du mouvement en passant les bons arguments
            self.app.db.add_movement(
                product_id=product["id"],
                shop_id=shop["id"],
                mtype=self.mtype,
                qty_kg=total_qty_kg,
                unit_price_kg=price_kg,
                note=note
            )
            
            if self.on_saved:
                self.on_saved()
            self.destroy()

        except Exception as e:
            Messagebox.show_error(f"Une erreur est survenue: {e}", "Erreur d'enregistrement")



class LoginDialog(ttk.Toplevel):
    """
    Boîte de dialogue de connexion modale.
    
    Args:
        parent: La fenêtre parent (instance de App).
        on_login (callable): La fonction à appeler après une connexion réussie.
    """
    def __init__(self, parent, on_login):
        super().__init__(parent)
        self.title("Authentification requise")
        self.transient(parent)
        self.grab_set()

        self.on_login = on_login

        frm = ttk.Frame(self, padding=20)
        frm.pack()

        ttk.Label(frm, text="Entrez votre code d'accès :").pack(pady=(0, 10))
        
        self.code_var = ttk.StringVar()
        entry = ttk.Entry(frm, textvariable=self.code_var, show="*")
        entry.pack(fill=X)
        entry.bind("<Return>", lambda e: self.save())

        btns = ttk.Frame(frm)
        btns.pack(pady=10)
        ttk.Button(btns, text="Se connecter", bootstyle="success", command=self.save).pack()

        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def save(self):
        """Valide le code et appelle la fonction de connexion."""
        code = self.code_var.get().strip()
        if code == "a":
            self.on_login("a")
            self.destroy()
        elif code == "secretaire":
            self.on_login("secretaire")
            self.destroy()
        else:
            Messagebox.show_error("Code d'accès invalide. Veuillez réessayer.", "Erreur d'authentification", parent=self)
            self.code_var.set("") # Vide le champ

    def on_close(self):
        """Gère la fermeture de la fenêtre (ferme toute l'application)."""
        if Messagebox.okcancel("Quitter l'application ? Les modifications non sauvegardées seront perdues.", "Confirmation", parent=self):
            self.master.destroy()

















