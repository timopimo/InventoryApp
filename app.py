from __future__ import annotations

import os
import sqlite3
from pathlib import Path
from typing import Any

from flask import Flask, jsonify, render_template, request

BASE_DIR = Path(__file__).resolve().parent
DEFAULT_DB_PATH = BASE_DIR / "data" / "inventory.db"


SEED_PRODUCTS = [
    ("Apple iPhone 15", "Electronics", 12),
    ("Samsung Galaxy S24", "Electronics", 9),
    ("Sony WH-1000XM5 Headphones", "Electronics", 18),
    ("Dell XPS 13 Laptop", "Computers", 7),
    ("Logitech MX Master 3S Mouse", "Computers", 25),
    ("Mechanical Keyboard", "Computers", 20),
    ("Nike Running Shoes", "Footwear", 30),
    ("Adidas Hoodie", "Apparel", 22),
    ("Levi's Jeans", "Apparel", 16),
    ("Instant Coffee", "Groceries", 40),
    ("Green Tea Pack", "Groceries", 35),
    ("Organic Almonds", "Groceries", 28),
    ("Ceramic Dinner Set", "Home", 11),
    ("Air Fryer", "Home Appliances", 10),
    ("Vacuum Cleaner", "Home Appliances", 8),
    ("Yoga Mat", "Fitness", 24),
    ("Dumbbell Set", "Fitness", 14),
    ("Mountain Bike Helmet", "Sports", 13),
    ("Desk Lamp", "Home", 19),
    ("Water Bottle", "Accessories", 50),
]


def create_app(test_config: dict[str, Any] | None = None) -> Flask:
    app = Flask(__name__)
    app.config.from_mapping(DB_PATH=str(DEFAULT_DB_PATH))

    if test_config:
        app.config.update(test_config)

    def get_db_connection() -> sqlite3.Connection:
        db_path = Path(app.config["DB_PATH"])
        db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def init_db() -> None:
        with get_db_connection() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS products (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    category TEXT NOT NULL,
                    quantity INTEGER NOT NULL CHECK(quantity >= 0)
                )
                """
            )
            count = conn.execute("SELECT COUNT(*) FROM products").fetchone()[0]
            if count == 0:
                conn.executemany(
                    "INSERT INTO products(name, category, quantity) VALUES (?, ?, ?)",
                    SEED_PRODUCTS,
                )
            conn.commit()

    app.init_db = init_db  # type: ignore[attr-defined]

    @app.route("/")
    def index() -> str:
        return render_template("index.html")

    @app.route("/api/products", methods=["GET"])
    def list_products() -> Any:
        with get_db_connection() as conn:
            rows = conn.execute(
                "SELECT id, name, category, quantity FROM products ORDER BY id"
            ).fetchall()
        return jsonify([dict(row) for row in rows])

    @app.route("/api/products", methods=["POST"])
    def add_product() -> Any:
        data = request.get_json(silent=True) or {}
        name = str(data.get("name", "")).strip()
        category = str(data.get("category", "")).strip()
        quantity = data.get("quantity", 0)

        if not name or not category:
            return jsonify({"error": "Name and category are required."}), 400

        try:
            quantity = int(quantity)
        except (ValueError, TypeError):
            return jsonify({"error": "Quantity must be an integer."}), 400

        if quantity < 0:
            return jsonify({"error": "Quantity cannot be negative."}), 400

        with get_db_connection() as conn:
            cursor = conn.execute(
                "INSERT INTO products(name, category, quantity) VALUES (?, ?, ?)",
                (name, category, quantity),
            )
            conn.commit()
            product_id = cursor.lastrowid
            row = conn.execute(
                "SELECT id, name, category, quantity FROM products WHERE id = ?",
                (product_id,),
            ).fetchone()
        return jsonify(dict(row)), 201

    @app.route("/api/products/<int:product_id>", methods=["DELETE"])
    def delete_product(product_id: int) -> Any:
        with get_db_connection() as conn:
            cursor = conn.execute("DELETE FROM products WHERE id = ?", (product_id,))
            conn.commit()
            if cursor.rowcount == 0:
                return jsonify({"error": "Product not found."}), 404
        return "", 204

    @app.route("/api/products/<int:product_id>", methods=["PATCH"])
    def update_quantity(product_id: int) -> Any:
        data = request.get_json(silent=True) or {}

        if "quantity" not in data:
            return jsonify({"error": "Quantity is required."}), 400

        try:
            quantity = int(data["quantity"])
        except (ValueError, TypeError):
            return jsonify({"error": "Quantity must be an integer."}), 400

        if quantity < 0:
            return jsonify({"error": "Quantity cannot be negative."}), 400

        with get_db_connection() as conn:
            cursor = conn.execute(
                "UPDATE products SET quantity = ? WHERE id = ?",
                (quantity, product_id),
            )
            conn.commit()
            if cursor.rowcount == 0:
                return jsonify({"error": "Product not found."}), 404
            row = conn.execute(
                "SELECT id, name, category, quantity FROM products WHERE id = ?",
                (product_id,),
            ).fetchone()
        return jsonify(dict(row))

    with app.app_context():
        init_db()

    return app


app = create_app()


if __name__ == "__main__":
    app.run(debug=bool(os.getenv("FLASK_DEBUG")), host="0.0.0.0", port=5000)
