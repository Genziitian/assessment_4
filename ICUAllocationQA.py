import unittest
from ICUAllocation import ICUAllocationSystem

class TestICUAllocationSystem(unittest.TestCase):
    def setUp(self):
        # Initialize with exactly 2 beds for simple overflow testing
        self.sys = ICUAllocationSystem(total_beds=2)

    def test_normal_and_critical_patient_allocation(self):
        # Normal/Low severity case
        res1 = self.sys.register_and_allocate("P1", 45, 98, 75, 120, 36.8, [])
        self.assertEqual(res1, "Allocated: LOW")
        
        # Severe/Critical case (Low oxygen + High Heart rate)
        res2 = self.sys.register_and_allocate("P2", 68, 85, 130, 120, 36.8, ["Diabetes"])
        self.assertEqual(res2, "Allocated: CRITICAL")

    def test_no_icu_beds_and_waiting_list(self):
        # Fill both available beds
        self.sys.register_and_allocate("P1", 30, 98, 70, 120, 36.6, [])
        self.sys.register_and_allocate("P2", 40, 98, 70, 120, 36.6, [])
        
        # Third stable patient should be deferred to the waiting list
        res3 = self.sys.register_and_allocate("P3", 50, 98, 70, 120, 36.6, [])
        self.assertEqual(res3, "Placed on Waiting List")
        self.assertEqual(len(self.sys.waiting_list), 1)

    def test_emergency_case_override(self):
        # Occupy beds with low priority stable patients
        self.sys.register_and_allocate("P1", 25, 98, 70, 120, 36.5, [])
        self.sys.register_and_allocate("P2", 35, 98, 70, 120, 36.5, [])
        
        # Incoming emergency case triggers a bump override configuration
        res = self.sys.register_and_allocate("P3", 60, 98, 70, 120, 36.5, [], is_emergency=True)
        self.assertEqual(res, "Allocated via Override: CRITICAL")
        self.assertIn("P3", self.sys.allocated_beds)

    def test_duplicate_patient(self):
        self.sys.register_and_allocate("P1", 25, 98, 70, 120, 36.5, [])
        res = self.sys.register_and_allocate("P1", 25, 98, 70, 120, 36.5, [])
        self.assertEqual(res, "Rejected: Duplicate Patient ID")

    def test_invalid_vital_inputs(self):
        res1 = self.sys.register_and_allocate("P1", 25, 999, 70, 120, 36.5, []) # Bad oxygen
        res2 = self.sys.register_and_allocate("P2", 25, 95, -50, 120, 36.5, []) # Bad heart rate
        self.assertEqual(res1, "Rejected: Invalid Vitals Data")
        self.assertEqual(res2, "Rejected: Invalid Vitals Data")

    def test_priority_boundary_values(self):
        # Exactly score 60 threshold validation boundary check
        # oxygen < 90 (+40) + heart rate out of bounds (+20) = 60 (CRITICAL)
        score = self.sys.calculate_priority_score(89, 130, 120, 36.5)
        self.assertEqual(score, 60)
        self.assertEqual(self.sys.classify_patient(score), "CRITICAL")

if __name__ == "__main__":
    unittest.main()
