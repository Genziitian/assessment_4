from threading import Lock

class InventoryManagement:
    def __init__(self, reorder_threshold=10):
        # self.stock format: {product_id: {"Warehouse A": qty, "Warehouse B": qty, ...}}
        self.stock = {}
        self.suppliers = {} # {product_id: supplier_name}
        self.threshold = reorder_threshold
        self.lock = Lock()
        self.warehouses = ["Warehouse A", "Warehouse B", "Warehouse C"]

    def add_product(self, prod_id, supplier=None):
        with self.lock:
            if prod_id in self.stock: return False
            self.stock[prod_id] = {wh: 0 for wh in self.warehouses}
            if supplier: self.suppliers[prod_id] = supplier
            return True

    def restock(self, prod_id, wh_name, qty):
        if qty <= 0 or wh_name not in self.warehouses: return False
        with self.lock:
            if prod_id not in self.stock: return False
            self.stock[prod_id][wh_name] += qty
            return True

    def transfer_stock(self, prod_id, from_wh, to_wh, qty):
        if qty <= 0 or from_wh == to_wh or from_wh not in self.warehouses or to_wh not in self.warehouses: return False
        with self.lock:
            if prod_id not in self.stock or self.stock[prod_id][from_wh] < qty: return False
            self.stock[prod_id][from_wh] -= qty
            self.stock[prod_id][to_wh] += qty
            return True

    def find_warehouse_for_order(self, prod_id, qty):
        # Finds the first warehouse in priority order (A -> B -> C) that can fulfill the demand
        if prod_id not in self.stock: return None
        for wh in self.warehouses:
            if self.stock[prod_id][wh] >= qty: return wh
        return None

    def fulfill_order(self, prod_id, qty):
        if qty <= 0: return "Invalid Quantity"
        with self.lock:
            wh = self.find_warehouse_for_order(prod_id, qty)
            if not wh: return "Insufficient Inventory"
            self.stock[prod_id][wh] -= qty
            
            # Check low-stock detection across the entire system
            total_stock = sum(self.stock[prod_id].values())
            if total_stock <= self.threshold:
                return f"Fulfilled by {wh} (Low Stock Alert: Reorder Needed from {self.suppliers.get(prod_id, 'Unknown')})"
            return f"Fulfilled by {wh}"

    def trigger_reorder(self, prod_id, qty=50):
        # Simulates ordering fresh inventory from the registered supplier to Warehouse A
        if prod_id not in self.stock or prod_id not in self.suppliers: return "Invalid Product/Supplier"
        return f"Order placed for {qty} units of {prod_id} with {self.suppliers[prod_id]}."
