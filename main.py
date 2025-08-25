# Fichier: main.py
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from db import Database
from ui.dashboard import DashboardPage
from ui.products import ProductsPage
from ui.movements import MovementsPage
from ui.inventory import InventoryPage
from ui.reports import ReportsPage
from ui.settings import SettingsPage
from ui.dialogs import LoginDialog

class App(ttk.Window):
    def __init__(self):
        """Initialise l'application et lance la boîte de dialogue de connexion."""
        super().__init__(themename="flatly")
        self.title("Provenderie - Gestion")
        self.geometry("1280x800")
        self.minsize(1100, 700)

        self.db = Database("provenderie.db")
        self.role = None  # Variable pour stocker le rôle de l'utilisateur

        # Initialisation de la structure principale
        self._build_layout()
        
        # Lance la boîte de dialogue de connexion dès le démarrage
        self.start_login()

    def start_login(self):
        """Affiche la boîte de dialogue de connexion."""
        # Crée une instance de LoginDialog. Le constructeur de LoginDialog gère l'affichage de la fenêtre.
        LoginDialog(self, on_login=self.handle_login)

    def handle_login(self, role):
        """Gère la connexion réussie et construit l'interface principale."""
        self.role = role
        # Construit les éléments de l'interface qui nécessitent le rôle
        self._build_sidebar()
        self._build_content()
        # Affiche la page par défaut (Dashboard)
        self.show_page("dashboard")

    def _build_layout(self):
        """Construit la structure de base de la fenêtre (barre supérieure et corps)."""
        # Topbar
        top = ttk.Frame(self, padding=10)
        top.pack(fill=X)
        ttk.Label(top, text="Gestion Provenderie", font="-size 16 -weight bold").pack(side=LEFT)
        ttk.Button(top, text="Mode sombre", bootstyle="secondary-outline", command=self.toggle_theme).pack(side=RIGHT)

        # Body
        self.body = ttk.Frame(self)
        self.body.pack(fill=BOTH, expand=YES)
        # Placeholder pour le contenu pour l'instant
        self.body_placeholder = ttk.Frame(self.body)

    def _build_sidebar(self):
        """Construit le panneau latéral de navigation."""
        self.sidebar = ttk.Frame(self.body, width=250, padding=10)
        self.sidebar.pack(side=LEFT, fill=Y)

        items = [
            ("Dashboard", "dashboard", "secondary"),
            ("Produits", "products", "primary"),
            ("Mouvements", "movements", "info"),
            ("Inventaire", "inventory", "warning"),
            ("Rapports", "reports", "success"),
            ("Paramètres", "settings", "secondary"),
        ]
        for text, key, style in items:
            ttk.Button(self.sidebar, text=text, bootstyle=f"{style}-outline",
                       command=lambda k=key: self.show_page(k)).pack(fill=X, pady=6)

    def _build_content(self):
        """Construit le cadre de contenu principal."""
        # Correction : le cadre de contenu doit être un enfant de self.body
        self.content = ttk.Frame(self.body, padding=10)
        self.content.pack(side=LEFT, fill=BOTH, expand=YES)

    def show_page(self, key: str):
        """Affiche la page demandée et détruit l'ancienne."""
        # Détruit les widgets existants dans le cadre de contenu
        for w in self.content.winfo_children():
            w.destroy()

        # Crée la nouvelle page
        if key == "dashboard":
            page = DashboardPage(self.content, self)
        elif key == "products":
            page = ProductsPage(self.content, self)
        elif key == "movements":
            page = MovementsPage(self.content, self)
        elif key == "inventory":
            page = InventoryPage(self.content, self)
        elif key == "reports":
            page = ReportsPage(self.content, self)
        elif key == "settings":
            page = SettingsPage(self.content, self)
        else:
            page = ttk.Label(self.content, text="Page inconnue")

        page.pack(fill=BOTH, expand=YES)
        if hasattr(page, "on_show"):
            page.on_show()

    def toggle_theme(self):
        """Bascule entre les thèmes 'flatly' et 'darkly'."""
        if self.style.theme_use() == "darkly":
            self.style.theme_use("flatly")
        else:
            self.style.theme_use("darkly")

if __name__ == "__main__":
    App().mainloop()