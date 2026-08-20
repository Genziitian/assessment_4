import unittest
from InsuranceClaim import InsuranceClaimSystem

class TestInsuranceClaimSystem(unittest.TestCase):
    def setUp(self):
        self.sys = InsuranceClaimSystem()

    def test_valid_claim(self):
        # Happy path within bounds
        res = self.sys.process_claim("POL123", "C1", 2000.0, "2026-06-01", 0, 30, "Collision", True)
        self.assertEqual(res["status"], "APPROVED")
        self.assertEqual(res["deductible"], 200.0)
        self.assertEqual(res["insurance_payout"], 1800.0)

    def test_expired_policy(self):
        res = self.sys.process_claim("POL123", "C1", 1000.0, "2027-05-01", 0, 30, "Collision", True)
        self.assertEqual(res["status"], "REJECTED")

    def test_claim_before_policy_start(self):
        res = self.sys.process_claim("POL123", "C1", 1000.0, "2025-12-15", 0, 30, "Collision", True)
        self.assertEqual(res["status"], "REJECTED")

    def test_excessive_claim_amount(self):
        # Claim higher than 50k coverage limit triggers a review flag and caps payout calculation
        res = self.sys.process_claim("POL123", "C1", 60000.0, "2026-06-01", 0, 30, "Collision", True)
        self.assertEqual(res["status"], "MANUAL REVIEW")
        self.assertEqual(res["max_payable"], 50000.0)

    def test_missing_documents(self):
        # Lacking docs flags manual review via risk score injection
        res = self.sys.process_claim("POL123", "C1", 2000.0, "2026-06-01", 0, 30, "Collision", False)
        self.assertEqual(res["status"], "MANUAL REVIEW")
        self.assertTrue(res["fraud_risk_score"] >= 35)

    def test_multiple_previous_claims(self):
        # 4 historical claims pushes fraud points up
        res = self.sys.process_claim("POL123", "C1", 2000.0, "2026-06-01", 4, 30, "Collision", True)
        self.assertEqual(res["status"], "MANUAL REVIEW")

    def test_fraud_scenario(self):
        # Triggers: 1) Missing Docs (35) + 2) Right after activation (30) + 3) Within 30 days of another claim (25)
        res = self.sys.process_claim("POL123", "C1", 2000.0, "2026-01-05", 0, 30, "Collision", False)
        self.assertEqual(res["status"], "FRAUD SUSPECTED")

    def test_boundary_claim_amount(self):
        # Tests exactly at coverage limits 
        res = self.sys.process_claim("POL123", "C1", 50000.0, "2026-06-01", 0, 30, "Collision", True)
        self.assertEqual(res["status"], "APPROVED")

    def test_invalid_policy_number(self):
        res = self.sys.process_claim("FAKE999", "C1", 2000.0, "2026-06-01", 0, 30, "Collision", True)
        self.assertEqual(res["status"], "REJECTED")

    def test_invalid_incident_date(self):
        res = self.sys.process_claim("POL123", "C1", 2000.0, "2026-99-99", 0, 30, "Collision", True)
        self.assertEqual(res["status"], "REJECTED")

if __name__ == "__main__":
    unittest.main()
