import datetime

class DigitalWallet:
    def __init__(self, account_id, owner_name, pin, daily_limit=5000.0, large_tx_threshold=2000.0):
        self.account_id = account_id
        self.owner_name = owner_name
        self._pin = pin
        self.balance = 0.0
        self.daily_limit = daily_limit
        self.large_tx_threshold = large_tx_threshold
        
        self.transactions = []  # List of dicts: {'time': datetime, 'type': str, 'amount': float, 'status': str, 'details': str}
        self.failed_pin_attempts = 0
        self.is_locked = False

    def verify_pin(self, input_pin):
        if self.is_locked:
            return False
        if self._pin == input_pin:
            self.failed_pin_attempts = 0
            return True
        else:
            self.failed_pin_attempts += 1
            if self.failed_pin_attempts >= 3:
                self.is_locked = True
            return False

    def _get_daily_total(self, now):
        total = 0.0
        for tx in self.transactions:
            if tx['status'] == 'Success' and tx['type'] in ['Withdrawal', 'Transfer Out']:
                if tx['time'].date() == now.date():
                    total += tx['amount']
        return total

    def _check_velocity_fraud(self, now):
        ten_minutes_ago = now - datetime.timedelta(minutes=10)
        recent_txs = [tx for tx in self.transactions if tx['time'] >= ten_minutes_ago]
        return len(recent_txs) >= 5

    def deposit(self, amount, now=None):
        if now is None:
            now = datetime.datetime.now()
        
        if amount <= 0:
            self.transactions.append({'time': now, 'type': 'Deposit', 'amount': amount, 'status': 'Failed', 'details': 'Negative or zero amount'})
            return False, "Amount must be positive."
            
        self.balance += amount
        self.transactions.append({'time': now, 'type': 'Deposit', 'amount': amount, 'status': 'Success', 'details': 'Deposit successful'})
        return True, "Deposit successful."

    def withdraw(self, amount, pin, now=None):
        if now is None:
            now = datetime.datetime.now()

        if self.is_locked:
            return False, "Account is locked due to multiple failed PIN attempts."

        # Fraud Check: Multiple failed PIN attempts trigger before verification check
        if self.failed_pin_attempts >= 2: 
            # If they already failed twice, this 3rd attempt (if wrong) triggers flag
            pass 

        if not self.verify_pin(pin):
            self.transactions.append({'time': now, 'type': 'Withdrawal', 'amount': amount, 'status': 'Failed', 'details': 'Invalid PIN'})
            if self.is_locked:
                return False, "Invalid PIN. Account has been locked."
            return False, "Invalid PIN."

        if amount <= 0:
            self.transactions.append({'time': now, 'type': 'Withdrawal', 'amount': amount, 'status': 'Failed', 'details': 'Negative or zero amount'})
            return False, "Amount must be positive."

        if amount > self.balance:
            self.transactions.append({'time': now, 'type': 'Withdrawal', 'amount': amount, 'status': 'Failed', 'details': 'Insufficient balance'})
            return False, "Insufficient balance."

        # Limit Check
        if self._get_daily_total(now) + amount > self.daily_limit:
            self.transactions.append({'time': now, 'type': 'Withdrawal', 'amount': amount, 'status': 'Failed', 'details': 'Daily limit exceeded'})
            return False, "Daily transaction limit exceeded."

        # Fraud Detection Flags
        flags = []
        if amount >= self.large_tx_threshold:
            flags.append("Large Transaction")
        if self._check_velocity_fraud(now):
            flags.append("High Frequency (>5 tx in 10 mins)")
        if amount % 1000 == 999: # Example rule for unusual pattern / fractional mismatch
            flags.append("Unusual Transaction Amount Pattern")

        status = "Flagged/Suspicious" if flags else "Success"
        details = f"Withdrawal successful. Flags: {', '.join(flags)}" if flags else "Withdrawal successful."

        self.balance -= amount
        self.transactions.append({'time': now, 'type': 'Withdrawal', 'amount': amount, 'status': status, 'details': details})
        return True, details

    def transfer(self, target_wallet, amount, pin, now=None):
        if now is None:
            now = datetime.datetime.now()

        if self.is_locked:
            return False, "Account is locked."

        if not self.verify_pin(pin):
            self.transactions.append({'time': now, 'type': 'Transfer Out', 'amount': amount, 'status': 'Failed', 'details': 'Invalid PIN'})
            return False, "Invalid PIN."

        if amount <= 0:
            self.transactions.append({'time': now, 'type': 'Transfer Out', 'amount': amount, 'status': 'Failed', 'details': 'Negative or zero amount'})
            return False, "Amount must be positive."

        if amount > self.balance:
            self.transactions.append({'time': now, 'type': 'Transfer Out', 'amount': amount, 'status': 'Failed', 'details': 'Insufficient balance'})
            return False, "Insufficient balance."

        if self._get_daily_total(now) + amount > self.daily_limit:
            self.transactions.append({'time': now, 'type': 'Transfer Out', 'amount': amount, 'status': 'Failed', 'details': 'Daily limit exceeded'})
            return False, "Daily transaction limit exceeded."

        # Fraud Detection Flags
        flags = []
        if amount >= self.large_tx_threshold:
            flags.append("Large Transaction")
        if self._check_velocity_fraud(now):
            flags.append("High Frequency (>5 tx in 10 mins)")

        status = "Flagged/Suspicious" if flags else "Success"
        details = f"Transfer successful. Flags: {', '.join(flags)}" if flags else "Transfer successful."

        self.balance -= amount
        self.transactions.append({'time': now, 'type': 'Transfer Out', 'amount': amount, 'status': status, 'details': f"Sent to {target_wallet.account_id}. {details}"})
        
        # Target wallet receives money
        target_wallet.balance += amount
        target_wallet.transactions.append({'time': now, 'type': 'Transfer In', 'amount': amount, 'status': 'Success', 'details': f"Received from {self.account_id}"})
        
        return True, details

    def get_history(self):
        return self.transactions

    def verify_balance(self):
        return self.balance
