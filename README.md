# InventoryApp

A simple and modern web app for managing retail inventory.

## Features

- Browse products in a table view
- Add new products
- Update product quantities
- Delete products
- Local SQLite database auto-created with 20 pre-populated products

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

Open http://127.0.0.1:5000

## Run tests

```bash
pytest
```
