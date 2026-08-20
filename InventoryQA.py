import unittest
import threading
from InventoryManagement import InventoryManagement

class TestInventoryManagement(unittest.TestCase):
    def setUp(self):
        self.im = InventoryManagement(reorder_threshold=5)
        self.im.add_product("Prod_X", supplier="Global Corp")
        self.im.add_product("Prod_Y", supplier="Logistics Inc")
        
        # Distribute inventory across different warehouses
        self.im.restock("Prod_X", "Warehouse A", 10)
        self.im.restock("Prod_X", "Warehouse B", 20)
        self.im.restock("Prod_Y", "Warehouse C", 4)

    def test_stock_availability_and_warehouse_selection(self):
        # Should auto-select Warehouse A first because it has enough stock (10 >= 5)
        self.assertEqual(self.im.fulfill_order("Prod_X", 5), "Fulfilled by Warehouse A")
        
        # Next order of 15 cannot fit in Warehouse A (now 5), should route to Warehouse B
        self.assertEqual(self.im.fulfill_order("Prod_X", 15), "Fulfilled by Warehouse B")

    def test_insufficient_inventory(self):
        # No single warehouse has 40 units
        self.assertEqual(self.im.fulfill_order("Prod_X", 40), "Insufficient Inventory")

    def test_warehouse_transfer(self):
        self.assertTrue(self.im.transfer_stock("Prod_X", "Warehouse B", "Warehouse C", 10))
        self.assertEqual(self.im.stock["Prod_X"]["Warehouse B"], 10)
        self.assertEqual(self.im.stock["Prod_X"]["Warehouse C"], 10)

    def test_reorder_threshold(self):
        # Prod_Y starts with 4 units total, which is already under the threshold of 5
        res = self.im.fulfill_order("Prod_Y", 2)
        self.assertIn("Low Stock Alert: Reorder Needed from Logistics Inc", res)
        self.assertEqual(self.im.trigger_reorder("Prod_Y"), "Order placed for 50 units of Prod_Y with Logistics Inc.")

    def test_invalid_product_and_negative_inventory(self):
        self.assertEqual(self.im.fulfill_order("Fake_Item", 5), "Insufficient Inventory")
        self.assertEqual(self.im.fulfill_order("Prod_X", -10), "Invalid Quantity")
        self.assertFalse(self.im.restock("Prod_X", "Warehouse A", -5))

    def test_concurrent_orders(self):
        # Warehouse A has 10 units. 5 threads trying to grab 2 units each at the same time.
        def customer():
            self.im.fulfill_order("Prod_X", 2)

        threads = [threading.Thread(target=customer) for _ in range(5)]
        for t in threads: t.start()
        for t in threads: t.join()
        
        # Warehouse A should be completely emptied out down to exactly 0
        self.assertEqual(self.im.stock["Prod_X"]["Warehouse A"], 0)

if __name__ == "__main__":
    unittest.main()
