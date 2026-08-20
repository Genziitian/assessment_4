import time
from threading import Lock

class DigitalWallet:
    def __init__(self, large_tx_thresh=10000, daily_limit=5000):
        self.accounts = {}       # Stores balance, PIN, and status
        self.history = {}        # Stores transaction timestamps and details
        self.failed_pins = {}    # Tracks consecutive bad PIN entries
        self.lock = Lock()       # Prevents errors during concurrent updates
        self.large_tx_thresh = large_tx_thresh
        self.daily_limit = daily_limit

    def create_account(self, acc_id, pin, initial_balance=0.0):
        with self.lock:
            if acc_id in self.accounts or initial_balance < 0: return False
            self.accounts[acc_id] = {"balance": initial_balance, "pin": pin, "locked": False}
            self.history[acc_id], self.failed_pins[acc_id] = [], 0
            return True

    def _is_fraud(self, acc_id, amount, action):
        now = time.time()
        recent = [t for t in self.history[acc_id] if now - t['time'] < 600]
        # Rule 1 & 2: Check velocity (5+ in 10 mins) and large transaction spikes
        if len(recent) >= 5 or amount > self.large_tx_thresh: return True
        # Rule 3: Check unusual amount (e.g., 3 standard deviations or just 3x average)
        if recent:
            avg = sum(t['amount'] for t in recent) / len(recent)
            if avg > 0 and amount > avg * 3: return True
        return False

    def _check_daily_limit(self, acc_id, amount):
        now = time.time()
        day_tx = [t['amount'] for t in self.history[acc_id] if now - t['time'] < 86400 and t['type'] in ['withdraw', 'transfer_out']]
        return (sum(day_tx) + amount) > self.daily_limit

    def authenticate(self, acc_id, pin):
        if acc_id not in self.accounts or self.accounts[acc_id]["locked"]: return False
        if self.accounts[acc_id]["pin"] == pin:
            self.failed_pins[acc_id] = 0
            return True
        self.failed_pins[acc_id] += 1
        if self.failed_pins[acc_id] >= 3: self.accounts[acc_id]["locked"] = True # Rule 4: Locked
        return False

    def transact(self, acc_id, pin, amount, action, target_id=None):
        if amount <= 0 or not self.authenticate(acc_id, pin): return "Auth/Input Error"
        with self.lock:
            acc = self.accounts[acc_id]
            if action in ['withdraw', 'transfer'] and acc['balance'] < amount: return "Insufficient Balance"
            if action in ['withdraw', 'transfer'] and self._check_daily_limit(acc_id, amount): return "Daily Limit Exceeded"
            
            is_suspicious = self._is_fraud(acc_id, amount, action)
            
            # Rule 5: Catch exact duplicate transactions within 5 seconds
            if self.history[acc_id] and (time.time() - self.history[acc_id][-1]['time'] < 5) and (self.history[acc_id][-1]['amount'] == amount) and (self.history[acc_id][-1]['type'] == action):
                is_suspicious = True

            if action == 'deposit': acc['balance'] += amount
            elif action == 'withdraw': acc['balance'] -= amount
            elif action == 'transfer':
                if target_id not in self.accounts: return "Target Missing"
                acc['balance'] -= amount
                self.accounts[target_id]['balance'] += amount
                self.history[target_id].append({'time': time.time(), 'amount': amount, 'type': 'transfer_in', 'flagged': is_suspicious})

            self.history[acc_id].append({'time': time.time(), 'amount': amount, 'type': f"{action}_out" if action == 'transfer' else action, 'flagged': is_suspicious})
            return "Flagged" if is_suspicious else "Success"

    def get_balance(self, acc_id, pin):
        return self.accounts[acc_id]['balance'] if self.authenticate(acc_id, pin) else None
