import sqlite3

from src import inventory


def test_check_stock_no_sql_injection(monkeypatch):
    """An SQL expression in product_id must not be interpreted as SQL."""
    connection = sqlite3.connect(":memory:")
    connection.execute("CREATE TABLE stock (pid INTEGER, qty INTEGER)")
    connection.execute("INSERT INTO stock VALUES (?, ?)", (1, 10))
    monkeypatch.setattr(inventory, "_conn", connection)

    try:
        assert inventory.check_stock("1 OR 1=1", 1) is False
    finally:
        connection.close()
