import sqlite3
from datetime import datetime
from typing import List, Dict, Optional, Tuple

class Database:
    def __init__(self, path: str = "provenderie.db"):
        self.path = path
        self.cnx = sqlite3.connect(self.path)
        self.cnx.row_factory = sqlite3.Row
        self.cnx.execute("PRAGMA foreign_keys = ON;")
        self.cnx.execute("PRAGMA journal_mode = WAL;")
        self._init_db()

    def _init_db(self):
        cur = self.cnx.cursor()
        cur.executescript("""
            CREATE TABLE IF NOT EXISTS shop (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                libelle TEXT NOT NULL UNIQUE
            );

            CREATE TABLE IF NOT EXISTS product (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sku TEXT UNIQUE,
                libelle TEXT NOT NULL,
                poids_sac_kg REAL NOT NULL DEFAULT 50,
                prix_kg REAL NOT NULL DEFAULT 0,
                prix_sac REAL NOT NULL DEFAULT 0,
                seuil_kg REAL NOT NULL DEFAULT 0,
                actif INTEGER NOT NULL DEFAULT 1
            );

            CREATE TABLE IF NOT EXISTS movement (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id INTEGER NOT NULL,
                shop_id INTEGER NOT NULL,
                type TEXT NOT NULL CHECK(type IN ('IN','OUT','ADJ')),
                qty_kg REAL NOT NULL,
                unit_price_kg REAL,
                note TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY(product_id) REFERENCES product(id),
                FOREIGN KEY(shop_id) REFERENCES shop(id)
            );
        """)
        cur.execute("INSERT OR IGNORE INTO shop(id, libelle) VALUES (1, 'Boutique Principale');")
        self.cnx.commit()

    # Shops
    def list_shops(self) -> List[Dict]:
        rows = self.cnx.execute("SELECT * FROM shop ORDER BY id").fetchall()
        return [dict(r) for r in rows]

    def add_shop(self, libelle: str):
        self.cnx.execute("INSERT INTO shop(libelle) VALUES (?)", (libelle,))
        self.cnx.commit()

    def rename_shop(self, shop_id: int, libelle: str):
        self.cnx.execute("UPDATE shop SET libelle=? WHERE id=?", (libelle, shop_id))
        self.cnx.commit()

    def delete_shop(self, shop_id: int) -> bool:
        in_use = self.cnx.execute("SELECT 1 FROM movement WHERE shop_id=? LIMIT 1", (shop_id,)).fetchone()
        if in_use:
            return False
        self.cnx.execute("DELETE FROM shop WHERE id=?", (shop_id,))
        self.cnx.commit()
        return True

    # Products
    def add_product(self, sku: Optional[str], libelle: str, poids_sac_kg: float, prix_kg: float, prix_sac: float, seuil_kg: float):
        self.cnx.execute(
            "INSERT INTO product(sku, libelle, poids_sac_kg, prix_kg, prix_sac, seuil_kg) VALUES (?,?,?,?,?,?)",
            (sku, libelle, float(poids_sac_kg), float(prix_kg), float(prix_sac), float(seuil_kg))
        )
        self.cnx.commit()

    def update_product(self, pid: int, sku: Optional[str], libelle: str, poids_sac_kg: float, prix_kg: float, prix_sac: float, seuil_kg: float, actif: int = 1):
        self.cnx.execute(
            """UPDATE product SET sku=?, libelle=?, poids_sac_kg=?, prix_kg=?, prix_sac=?, seuil_kg=?, actif=?
               WHERE id=?""",
            (sku, libelle, float(poids_sac_kg), float(prix_kg), float(prix_sac), float(seuil_kg), int(actif), pid)
        )
        self.cnx.commit()

    def archive_product(self, pid: int):
        self.cnx.execute("UPDATE product SET actif=0 WHERE id=?", (pid,))
        self.cnx.commit()

    def list_products(self, q: str = "", include_inactive: bool = False) -> List[Dict]:
        q = f"%{q.strip()}%" if q else "%"
        sql = "SELECT * FROM product WHERE (libelle LIKE ? OR ifnull(sku,'') LIKE ?)"
        params = [q, q]
        if not include_inactive:
            sql += " AND actif=1"
        sql += " ORDER BY libelle"
        rows = self.cnx.execute(sql, params).fetchall()
        return [dict(r) for r in rows]

    def get_product(self, pid: int) -> Optional[Dict]:
        r = self.cnx.execute("SELECT * FROM product WHERE id=?", (pid,)).fetchone()
        return dict(r) if r else None

    # Movements
    def add_movement(self, product_id: int, shop_id: int, mtype: str, qty_kg: float, note: str = "", unit_price_kg: Optional[float] = None):
        self.cnx.execute(
            "INSERT INTO movement(product_id, shop_id, type, qty_kg, unit_price_kg, note, created_at) VALUES (?,?,?,?,?,?,?)",
            (product_id, shop_id, mtype, float(qty_kg), unit_price_kg, note, datetime.now().isoformat(timespec="seconds"))
        )
        self.cnx.commit()

    def list_movements(self,
                       mtype: Optional[str] = None,
                       shop_id: Optional[int] = None,
                       q: str = "",
                       date_from: Optional[str] = None,
                       date_to: Optional[str] = None) -> List[Dict]:
        where = []
        params: List = []

        if mtype and mtype in ("IN", "OUT", "ADJ"):
            where.append("m.type = ?")
            params.append(mtype)
        if shop_id:
            where.append("m.shop_id = ?")
            params.append(shop_id)
        if q:
            where.append("(p.libelle LIKE ? OR ifnull(p.sku,'') LIKE ?)")
            params.extend([f"%{q.strip()}%", f"%{q.strip()}%"])
        if date_from:
            where.append("date(m.created_at) >= date(?)")
            params.append(date_from)
        if date_to:
            where.append("date(m.created_at) <= date(?)")
            params.append(date_to)

        sql = """
            SELECT m.*, p.libelle AS product_libelle, p.poids_sac_kg, s.libelle AS shop_libelle
            FROM movement m
            JOIN product p ON p.id = m.product_id
            JOIN shop s ON s.id = m.shop_id
        """
        if where:
            sql += " WHERE " + " AND ".join(where)
        sql += " ORDER BY m.created_at DESC, m.id DESC"

        rows = self.cnx.execute(sql, params).fetchall()
        return [dict(r) for r in rows]

    def stock_kg(self, product_id: int, shop_id: int = 1) -> float:
        row = self.cnx.execute(
            "SELECT COALESCE(SUM(qty_kg),0) AS s FROM movement WHERE product_id=? AND shop_id=?",
            (product_id, shop_id)
        ).fetchone()
        return float(row["s"] or 0.0)

    def all_stocks(self, shop_id: int = 1) -> List[Tuple[Dict, float]]:
        products = self.list_products()
        result = []
        for p in products:
            qty = self.stock_kg(p["id"], shop_id=shop_id)
            result.append((p, qty))
        return result

    def total_stock_kg(self, shop_id: int = 1) -> float:
        row = self.cnx.execute("SELECT COALESCE(SUM(qty_kg),0) AS s FROM movement WHERE shop_id=?", (shop_id,)).fetchone()
        return float(row["s"] or 0.0)

    def low_stock_products(self, shop_id: int = 1) -> List[Dict]:
        items = []
        for p, qty in self.all_stocks(shop_id=shop_id):
            if qty <= p.get("seuil_kg", 0):
                d = dict(p)
                d["stock_kg"] = qty
                items.append(d)
        return items