import heapq
from threading import Lock

class ICUAllocationSystem:
    def __init__(self, total_beds=5):
        self.total_beds = total_beds
        self.allocated_beds = {}   # {patient_id: {data}}
        self.waiting_list = []     # Min-heap queue elements sorted by priority score (lowest priority score gets inverted to behave as max-heap)
        self.all_patients = set()  # Track duplicate registration prevention
        self.lock = Lock()

    def calculate_priority_score(self, oxygen, heart_rate, bp_systolic, temp):
        # Validation checks for erratic or hazardous telemetry readings
        if not (0 <= oxygen <= 100) or not (0 <= heart_rate <= 300) or not (0 <= bp_systolic <= 300) or not (0 <= temp <= 50):
            return None

        score = 0
        # Score calculation rules based on severity
        if oxygen < 90: score += 40
        elif oxygen < 95: score += 20
        
        if heart_rate > 120 or heart_rate < 50: score += 20
        if bp_systolic > 160 or bp_systolic < 90: score += 20
        if temp > 39.0 or temp < 35.5: score += 20
        
        return score

    def classify_patient(self, score):
        if score >= 60: return "CRITICAL"
        if score >= 40: return "HIGH"
        if score >= 20: return "MEDIUM"
        return "LOW"

    def register_and_allocate(self, patient_id, age, oxygen, heart_rate, bp_systolic, temp, conditions, is_emergency=False):
        with self.lock:
            # 1. Prevent Duplicate Patient Registration
            if patient_id in self.all_patients:
                return "Rejected: Duplicate Patient ID"

            # 2. Calculate priority score and run input boundary sanitization 
            score = self.calculate_priority_score(oxygen, heart_rate, bp_systolic, temp)
            if score is None:
                return "Rejected: Invalid Vitals Data"

            classification = self.classify_patient(score)
            if is_emergency:
                classification = "CRITICAL"
                score = max(score, 80) # Force highest priority value block

            patient_data = {
                "id": patient_id, "age": age, "score": score, 
                "class": classification, "is_emergency": is_emergency
            }
            self.all_patients.add(patient_id)

            # 3. Check ICU Bed Availability & Allocation Logic
            if len(self.allocated_beds) < self.total_beds:
                self.allocated_beds[patient_id] = patient_data
                return f"Allocated: {classification}"

            # 4. Emergency Case Override Logic
            if is_emergency or classification == "CRITICAL":
                # Find the lowest priority patient currently occupying a bed
                lowest_allocated = min(self.allocated_beds.values(), key=lambda x: (x["is_emergency"], x["score"]))
                
                # Kick them out to the waiting list if the new patient is higher risk
                if not lowest_allocated["is_emergency"] or (is_emergency and not lowest_allocated["is_emergency"]):
                    kicked_patient = self.allocated_beds.pop(lowest_allocated["id"])
                    
                    # Push kicked patient to waitlist
                    heapq.heappush(self.waiting_list, (-kicked_patient["score"], kicked_patient["id"], kicked_patient))
                    
                    # Seat the new critical/emergency patient
                    self.allocated_beds[patient_id] = patient_data
                    return f"Allocated via Override: {classification}"

            # 5. Place on Waiting List
            heapq.heappush(self.waiting_list, (-score, patient_id, patient_data))
            return "Placed on Waiting List"
