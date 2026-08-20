import unittest
import threading
import time
from DigitalWallet import DigitalWallet

class TestWalletSecurity(unittest.TestCase):
    def setUp(self):
        self.w = DigitalWallet(large_tx_thresh=1000, daily_limit=500)
        self.w.create_account("A", "1234", 100.0)
        self.w.create_account("B", "5678", 50.0)

    def test_normal_transaction(self):
        self.assertEqual(self.w.transact("A", "1234", 20, "deposit"), "Success")
        self.assertEqual(self.w.get_balance("A", "1234"), 120.0)

    def test_insufficient_balance(self):
        self.assertEqual(self.w.transact("A", "1234", 200, "withdraw"), "Insufficient Balance")

    def test_daily_limit(self):
        self.w.create_account("C", "1111", 1000.0)
        self.assertEqual(self.w.transact("C", "1111", 400, "withdraw"), "Success")
        self.assertEqual(self.w.transact("C", "1111", 200, "withdraw"), "Daily Limit Exceeded")

    def test_failed_pins(self):
        for _ in range(2): self.w.authenticate("A", "9999")
        self.assertFalse(self.w.accounts["A"]["locked"])
        self.w.authenticate("A", "9999")
        self.assertTrue(self.w.accounts["A"]["locked"])

    def test_suspicious_and_duplicate(self):
        # Test large transaction flag
        self.assertEqual(self.w.transact("A", "1234", 1500, "deposit"), "Flagged")
        # Test duplicate transaction check
        self.w.transact("B", "5678", 10, "deposit")
        self.assertEqual(self.w.transact("B", "5678", 10, "deposit"), "Flagged")

    def test_negative_amount(self):
        self.assertEqual(self.w.transact("A", "1234", -50, "deposit"), "Auth/Input Error")

    def test_concurrent_transactions(self):
        def worker():
            for _ in range(5): self.w.transact("A", "1234", 1, "withdraw")
        threads = [threading.Thread(target=worker) for _ in range(5)]
        for t in threads: t.start()
        for t in threads: t.join()
        self.assertEqual(self.w.get_balance("A", "1234"), 75.0)

if __name__ == "__main__":
    unittest.main()
