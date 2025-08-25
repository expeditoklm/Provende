import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from ttkbootstrap.dialogs import Messagebox
from .base import BasePage

class SettingsPage(BasePage):
    def on_show(self):
        self.build()
        self.refresh()

    def build(self):
        for w in self.winfo_children():
            w.destroy()

        header = ttk.Frame(self); header.pack(fill=X)
        ttk.Label(header, text="Paramètres", font="-size 14 -weight bold").pack(side=LEFT)
        ttk.Button(header, text="Basculer thème", bootstyle="secondary", command=self.app.toggle_theme).pack(side=RIGHT)

        ttk.Separator(self).pack(fill=X, pady=10)

        # Shops management
        box = ttk.Labelframe(self, text="Boutiques")
        box.pack(fill=BOTH, expand=YES, padx=5, pady=5)

        left = ttk.Frame(box); left.pack(side=LEFT, fill=Y, padx=10, pady=10)
        self.shop_list = ttk.Treeview(left, columns=("id","libelle"), show="headings", height=15)
        self.shop_list.heading("id", text="ID")
        self.shop_list.heading("libelle", text="Libellé")
        self.shop_list.column("id", width=60, anchor=CENTER)
        self.shop_list.column("libelle", width=260, anchor=W)
        self.shop_list.pack(fill=Y)

        right = ttk.Frame(box); right.pack(side=LEFT, fill=BOTH, expand=YES, padx=10, pady=10)
        self.shop_name_var = ttk.StringVar()
        row = ttk.Frame(right); row.pack(fill=X, pady=6)
        ttk.Label(row, text="Libellé").pack(side=LEFT, padx=(0,6))
        ttk.Entry(row, textvariable=self.shop_name_var, width=30).pack(side=LEFT)

        btns = ttk.Frame(right); btns.pack(fill=X, pady=10)
        ttk.Button(btns, text="Ajouter", bootstyle="success", command=self.add_shop).pack(side=LEFT, padx=5)
        ttk.Button(btns, text="Renommer", bootstyle="secondary", command=self.rename_shop).pack(side=LEFT, padx=5)
        ttk.Button(btns, text="Supprimer", bootstyle="danger", command=self.delete_shop).pack(side=LEFT, padx=5)

    def refresh(self):
        for i in self.shop_list.get_children():
            self.shop_list.delete(i)
        for s in self.app.db.list_shops():
            self.shop_list.insert("", END, values=(s["id"], s["libelle"]))

    def selected_shop(self):
        sel = self.shop_list.focus()
        if not sel:
            return None
        vals = self.shop_list.item(sel, "values")
        return {"id": int(vals[0]), "libelle": vals[1]}

    def add_shop(self):
        name = self.shop_name_var.get().strip()
        if not name:
            Messagebox.show_error("Libellé requis.", "Erreur")
            return
        try:
            self.app.db.add_shop(name)
            self.shop_name_var.set("")
            self.refresh()
        except Exception as e:
            Messagebox.show_error(str(e), "Erreur")

    def rename_shop(self):
        shop = self.selected_shop()
        if not shop:
            Messagebox.show_warning("Sélectionne une boutique.", "Info")
            return
        name = self.shop_name_var.get().strip()
        if not name:
            Messagebox.show_error("Saisis un nouveau libellé.", "Erreur")
            return
        try:
            self.app.db.rename_shop(shop["id"], name)
            self.refresh()
        except Exception as e:
            Messagebox.show_error(str(e), "Erreur")

    def delete_shop(self):
        shop = self.selected_shop()
        if not shop:
            Messagebox.show_warning("Sélectionne une boutique.", "Info")
            return
        if not Messagebox.okcancel(f"Supprimer la boutique '{shop['libelle']}' ?", "Confirmer"):
            return
        ok = self.app.db.delete_shop(shop["id"])
        if not ok:
            Messagebox.show_error("Impossible: des mouvements y sont rattachés.", "Erreur")
        self.refresh()