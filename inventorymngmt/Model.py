import datetime

class Product:
    def __init__(
        self,
        name,
        sku,
        quantity,
        min_stock,
        category="",
        location="",
        created_at=None,
        updated_at=None,
        id=None,
    ):
        self.name = name
        self.sku = sku
        self.quantity = quantity
        self.min_stock = min_stock
        self.category = category
        self.location = location
        self.created_at = created_at if created_at is not None else datetime.datetime.now().isoformat()
        self.updated_at = updated_at if updated_at is not None else datetime.datetime.now().isoformat()
        self.id = id



