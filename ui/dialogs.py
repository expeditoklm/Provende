import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from ttkbootstrap.dialogs import QueryDialog ,Messagebox
from utils import safe_float
from ttkbootstrap import DateEntry
from typing import Optional, Dict
from utils import kg_to_bag_repr

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
    def __init__(self, parent, on_saved, movement_data=None, product=None, mtype=None, shop=None):
        """
        Initialise le dialogue de mouvement.
        
        :param parent: La fenêtre parente (généralement la fenêtre principale de l'application).
        :param on_saved: La fonction de rappel à exécuter après un enregistrement réussi.
        :param movement_data: (Optionnel) Un dictionnaire contenant les données d'un mouvement existant à modifier.
        """
        super().__init__(parent)
        self.transient(parent)
        self.resizable(False, False)
        self.grab_set()
        
        self.app = parent
        self.on_saved = on_saved
        self.movement_data = movement_data
        
        # Initialise les attributs de la classe en fonction des données fournies
        if self.movement_data:
            self.product = self.app.db.get_product(self.movement_data['product_id'])
            self.mtype = self.movement_data.get('type')  # Utilisation de 'type' qui est le nom de la colonne
            self.shop = self.app.db.get_shop(self.movement_data.get('shop_id'))
            
            # Ajuster les quantités pour l'affichage
            self.qty_kg_total = self.movement_data.get('qty_kg', 0.0)
            
            self.sacs_qty_value = 0.0
            self.kg_qty_value = 0.0
            if self.product and self.product.get("poids_sac_kg", 0) > 0:
                self.sacs_qty_value = int(abs(self.qty_kg_total) / self.product["poids_sac_kg"])
                self.kg_qty_value = abs(self.qty_kg_total) % self.product["poids_sac_kg"]
            else:
                self.kg_qty_value = abs(self.qty_kg_total)

            self.sac_price_value = self.movement_data.get('unit_price_sac', 0.0)
            self.kg_price_value = self.movement_data.get('unit_price_kg', 0.0)
            self.note_value = self.movement_data.get('note', '')

        else: # Nouvel enregistrement, utiliser les valeurs initiales ou celles passées en argument
            self.product = product
            self.mtype = mtype
            self.shop = shop
            self.sacs_qty_value = 0.0
            self.kg_qty_value = 0.0
            self.sac_price_value = 0.0
            self.kg_price_value = 0.0
            self.note_value = ''

        # Configuration du titre de la fenêtre
        self.title_text = "Nouveau mouvement"
        if self.movement_data:
            self.title_text = "Modifier le mouvement"
        elif self.product:
            self.title_text = f"Nouveau mouvement pour {self.product['libelle']}"
        self.title(self.title_text)

        self.protocol("WM_DELETE_WINDOW", self.on_cancel)

        # --- Construction de l'UI ---
        padding = (10, 10)
        main_frame = ttk.Frame(self, padding=padding)
        main_frame.pack(fill=BOTH, expand=YES)

        # Section de sélection de produit
        if not self.product:
            ttk.Label(main_frame, text="Produit").pack(anchor=W)
            self.product_search_var = ttk.StringVar()
            self.product_entry = ttk.Entry(main_frame, textvariable=self.product_search_var, width=50)
            self.product_entry.pack(fill=X, pady=(0, 10))
            self.product_entry.bind("<KeyRelease>", self.on_product_search)
            
            self.product_listbox = ttk.Treeview(main_frame, columns=["libelle"], show="headings", height=5)
            self.product_listbox.heading("libelle", text="Sélectionnez un produit")
            self.product_listbox.pack(fill=X)
            self.product_listbox.bind("<<TreeviewSelect>>", self.on_product_select)
            self.product_listbox.bind("<Double-1>", self.on_double_click)
            self.product_entry.focus_set()
            self.update_product_list()
        else:
            ttk.Label(main_frame, text="Produit :", font="-size 10 -weight bold").pack(anchor=W)
            ttk.Label(main_frame, text=self.product["libelle"]).pack(anchor=W)

        # Cadre pour les détails du mouvement
        details_frame = ttk.Frame(main_frame)
        details_frame.pack(fill=X, pady=10)

        # Labels et Combobox pour le type de mouvement
        ttk.Label(details_frame, text="Type de mouvement").grid(row=0, column=0, sticky=W, padx=(0,10))
        self.mtype_var = ttk.StringVar(value=self.mtype or "IN")
        self.mtype_combo = ttk.Combobox(details_frame, values=["IN", "OUT", "ADJ"], textvariable=self.mtype_var, state="readonly")
        self.mtype_combo.grid(row=0, column=1, sticky=EW)
        
        # Labels et Combobox pour la boutique
        ttk.Label(details_frame, text="Boutique").grid(row=1, column=0, sticky=W, padx=(0,10), pady=(10,0))
        self.shop_var = ttk.StringVar(value=self.shop["libelle"] if self.shop else "Boutique Principale")
        shops = self.app.db.list_shops()
        shop_names = [s["libelle"] for s in shops]
        self.shop_combo = ttk.Combobox(details_frame, values=shop_names, textvariable=self.shop_var, state="readonly")
        self.shop_combo.grid(row=1, column=1, sticky=EW, pady=(10,0))
        self.shop_ids = {s["libelle"]: s["id"] for s in shops}
        
        # Cadre pour les quantités (sacs et kg)
        qty_frame = ttk.Frame(main_frame)
        qty_frame.pack(fill=X, pady=10)

        ttk.Label(qty_frame, text="Qté (sacs)").grid(row=0, column=0, sticky=W, padx=(0,10))
        self.sacs_qty_var = ttk.DoubleVar(value=self.sacs_qty_value)
        self.sacs_qty_entry = ttk.Entry(qty_frame, textvariable=self.sacs_qty_var)
        self.sacs_qty_entry.grid(row=0, column=1, sticky=EW)
        
        ttk.Label(qty_frame, text="Qté (kg)").grid(row=1, column=0, sticky=W, padx=(0,10), pady=(10,0))
        self.kg_qty_var = ttk.DoubleVar(value=self.kg_qty_value)
        self.kg_qty_entry = ttk.Entry(qty_frame, textvariable=self.kg_qty_var)
        self.kg_qty_entry.grid(row=1, column=1, sticky=EW, pady=(10,0))
        
        # Cadre pour les prix unitaires
        price_frame = ttk.Frame(main_frame)
        price_frame.pack(fill=X, pady=10)
        
        ttk.Label(price_frame, text="Prix/sac (FCFA)").grid(row=0, column=0, sticky=W, padx=(0,10))
        self.sac_price_var = ttk.DoubleVar(value=self.sac_price_value)
        self.sac_price_entry = ttk.Entry(price_frame, textvariable=self.sac_price_var)
        self.sac_price_entry.grid(row=0, column=1, sticky=EW)

        ttk.Label(price_frame, text="Prix/kg (FCFA)").grid(row=1, column=0, sticky=W, padx=(0,10), pady=(10,0))
        self.kg_price_var = ttk.DoubleVar(value=self.kg_price_value)
        self.kg_price_entry = ttk.Entry(price_frame, textvariable=self.kg_price_var)
        self.kg_price_entry.grid(row=1, column=1, sticky=EW, pady=(10,0))

        # Champ de note
        ttk.Label(main_frame, text="Note (facultatif)").pack(anchor=W, pady=(10,0))
        self.note_entry = ttk.Text(main_frame, height=3, width=50)
        self.note_entry.pack(fill=X)
        if self.note_value:
            self.note_entry.insert("1.0", self.note_value)

        # Boutons d'action
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=X, pady=(20, 0))
        ttk.Button(button_frame, text="Annuler", bootstyle="secondary", command=self.on_cancel).pack(side=RIGHT)
        ttk.Button(button_frame, text="Enregistrer", bootstyle="success", command=self.on_save).pack(side=RIGHT, padx=(0, 10))

    def on_product_search(self, event=None):
        q = self.product_search_var.get()
        products = self.app.db.list_products(q=q)
        self.product_listbox.delete(*self.product_listbox.get_children())
        for p in products:
            self.product_listbox.insert("", END, iid=p["id"], values=[f"{p['libelle']} (SKU: {p['sku']})"])

    def on_product_select(self, event):
        item_id = self.product_listbox.focus()
        if item_id:
            product_id = int(item_id)
            self.product = self.app.db.get_product(product_id)
            self.title(f"Nouveau mouvement pour {self.product['libelle']}")

    def on_double_click(self, event):
        item = self.product_listbox.identify('item', event.x, event.y)
        if item:
            self.on_product_select(event)
            self.on_save()

    def on_save(self):
        if not self.product:
            Messagebox.show_error("Veuillez sélectionner un produit.", "Erreur de saisie")
            return

        try:
            num_bags = self.sacs_qty_var.get()
            num_kg = self.kg_qty_var.get()
            
            # Déterminer la quantité totale en kg
            qty_kg_total = 0.0
            if self.product["poids_sac_kg"] > 0 and num_bags > 0:
                qty_kg_total += num_bags * self.product["poids_sac_kg"]
            
            qty_kg_total += num_kg
            
            if qty_kg_total <= 0:
                Messagebox.show_error("La quantité totale doit être supérieure à 0.", "Erreur de saisie")
                return

            mtype = self.mtype_var.get()
            shop_name = self.shop_var.get()
            shop_id = self.shop_ids.get(shop_name)
            
            unit_price_sac = self.sac_price_var.get()
            unit_price_kg = self.kg_price_var.get()

            # Calcul du coût total selon les règles
            cost = 0.0
            if num_bags > 0 and unit_price_sac > 0:
                cost += num_bags * unit_price_sac
            if num_kg > 0 and unit_price_kg > 0:
                cost += num_kg * unit_price_kg
            # Si un seul type de prix est renseigné pour une quantité, le coût est calculé sur cette base
            if num_bags > 0 and num_kg == 0 and unit_price_sac > 0 and unit_price_kg <= 0:
                cost = num_bags * unit_price_sac
            elif num_kg > 0 and num_bags == 0 and unit_price_kg > 0 and unit_price_sac <= 0:
                cost = num_kg * unit_price_kg

            note = self.note_entry.get("1.0", END).strip()
            
            # Gestion des mouvements 'OUT'
            if mtype == "OUT":
                qty_kg_total = -qty_kg_total

            # Vérifier si c'est une mise à jour ou un nouvel enregistrement
            if self.movement_data:
                # Mise à jour du mouvement existant
                self.app.db.update_movement(
                    mid=self.movement_data.get('id'), # Correction ici: utilisation de 'mid'
                    product_id=self.product["id"],
                    shop_id=shop_id,
                    mtype=mtype,
                    qty_kg=qty_kg_total,
                    unit_price_kg=unit_price_kg if unit_price_kg > 0 else None,
                    unit_price_sac=unit_price_sac if unit_price_sac > 0 else None,
                    cost=cost,
                    note=note
                )
            else:
                # Enregistrement d'un nouveau mouvement
                self.app.db.add_movement(
                    product_id=self.product["id"],
                    shop_id=shop_id,
                    mtype=mtype,
                    qty_kg=qty_kg_total,
                    unit_price_kg=unit_price_kg if unit_price_kg > 0 else None,
                    unit_price_sac=unit_price_sac if unit_price_sac > 0 else None,
                    cost=cost,
                    note=note
                )
            
            self.result = "saved"
            self.on_saved()
            self.destroy()

        except ValueError:
            Messagebox.show_error("Veuillez entrer des valeurs numériques valides pour les quantités et les prix.", "Erreur de saisie")

    def on_cancel(self):
        self.destroy()


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
