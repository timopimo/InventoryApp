from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[1]))
from app import create_app


def create_test_client(tmp_path: Path):
    db_path = tmp_path / "test_inventory.db"
    app = create_app({"TESTING": True, "DB_PATH": str(db_path)})
    return app.test_client()


def test_seed_data_contains_20_products(tmp_path):
    client = create_test_client(tmp_path)

    response = client.get("/api/products")

    assert response.status_code == 200
    products = response.get_json()
    assert len(products) == 20


def test_add_update_delete_product(tmp_path):
    client = create_test_client(tmp_path)

    add_response = client.post(
        "/api/products",
        json={"name": "USB-C Cable", "category": "Accessories", "quantity": 15},
    )
    assert add_response.status_code == 201
    added = add_response.get_json()

    update_response = client.patch(
        f"/api/products/{added['id']}",
        json={"quantity": 3},
    )
    assert update_response.status_code == 200
    assert update_response.get_json()["quantity"] == 3

    delete_response = client.delete(f"/api/products/{added['id']}")
    assert delete_response.status_code == 204


def test_reject_negative_quantity(tmp_path):
    client = create_test_client(tmp_path)

    response = client.post(
        "/api/products",
        json={"name": "Unsafe Product", "category": "Test", "quantity": -1},
    )

    assert response.status_code == 400
