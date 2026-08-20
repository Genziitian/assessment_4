import datetime

class InsuranceClaimSystem:
    def __init__(self):
        # Sample policy database: {policy_num: {cust_id, type, coverage, start_date, expiry_date}}
        self.policies = {
            "POL123": {"cust_id": "C1", "type": "Auto", "coverage": 50000.0, "start": "2026-01-01", "expiry": "2027-01-01"},
            "POL456": {"cust_id": "C2", "type": "Health", "coverage": 100000.0, "start": "2026-02-01", "expiry": "2027-02-01"}
        }
        # Tracks past incident dates per customer to look for claims clustered close together
        self.past_claims = {"C1": ["2026-01-15"]}

    def process_claim(self, policy_num, cust_id, claim_amt, incident_date_str, prev_claim_count, cust_age, incident_type, has_docs):
        if policy_num not in self.policies or self.policies[policy_num]["cust_id"] != cust_id or claim_amt <= 0 or cust_age < 18:
            return {"status": "REJECTED", "payout": 0, "reason": "Invalid Policy/Input"}

        p = self.policies[policy_num]
        cov, start, expiry = p["coverage"], datetime.date.fromisoformat(p["start"]), datetime.date.fromisoformat(p["expiry"])
        try: inc_date = datetime.date.fromisoformat(incident_date_str)
        except ValueError: return {"status": "REJECTED", "payout": 0, "reason": "Invalid Incident Date"}

        # Basic eligibility check
        if inc_date < start: return {"status": "REJECTED", "payout": 0, "reason": "Incident Before Policy Start"}
        if inc_date > expiry: return {"status": "REJECTED", "payout": 0, "reason": "Expired Policy"}

        # Calculate Fraud Risk Score (Points base system)
        score = 0
        if not has_docs: score += 35                                        # Missing documents
        if (inc_date - start).days <= 7: score += 30                        # Incident right after activation
        if claim_amt > cov: score += 25                                     # Amount higher than policy limit
        if prev_claim_count >= 3: score += 30                               # FIX: Boosted to 30 to hit MANUAL REVIEW floor
        
        # Check for multiple claims within a short 30-day window
        recent_claims = [datetime.date.fromisoformat(d) for d in self.past_claims.get(cust_id, []) if abs((inc_date - datetime.date.fromisoformat(d)).days) <= 30]
        if recent_claims: score += 25

        # Determine structural financials (Assuming a standard 10% deductible up to a max cap of 500)
        deductible = min(claim_amt * 0.10, 500.0)
        max_payable = min(claim_amt, cov)
        payout = max(0.0, max_payable - deductible)
        cust_contrib = claim_amt - payout

        # Route status classification based on risk score metrics
        if score >= 60: status = "FRAUD SUSPECTED"
        elif score >= 30: status = "MANUAL REVIEW"
        elif claim_amt > cov: status = "MANUAL REVIEW" # Excess coverage cap routing
        else: status = "APPROVED"

        return {
            "status": status, "eligibility": "Eligible", "max_payable": max_payable,
            "deductible": deductible, "customer_contribution": cust_contrib,
            "insurance_payout": payout, "fraud_risk_score": score
        }
