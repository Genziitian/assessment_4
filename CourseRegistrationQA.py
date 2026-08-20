import unittest
from CourseRegistration import CourseRegistrationSystem

class TestCourseRegistration(unittest.TestCase):
    def setUp(self):
        # Initialize system with a strict 12 credit cap for boundary testing
        self.crs = CourseRegistrationSystem(max_credits_default=12)
        
        # Setup student with basic programming completion background
        self.crs.add_student("STU01", completed_courses=["Programming"], current_semester=3)
        self.crs.add_student("STU02", completed_courses=["Data Structures", "Statistics"], current_semester=4)

    def test_valid_registration(self):
        # STU01 has 'Programming', DBMS requires 'Programming'
        res = self.crs.register_courses("STU01", ["DBMS"])
        self.assertIn("Success", res)
        self.assertEqual(self.crs.get_registered_credits("STU01"), 4)

    def test_missing_prerequisite(self):
        # AI requires 'Data Structures', STU01 only has 'Programming'
        res = self.crs.register_courses("STU01", ["AI"])
        self.assertIn("Missing prerequisite 'Data Structures'", res)

    def test_credit_limit_and_boundary_values(self):
        # Add 'Programming' so STU02 meets the prerequisite for DBMS
        self.crs.students["STU02"]["completed"].append("Programming")
        
        # STU02 attempts: AI (4) + DBMS (4) = 8 credits (Under 12 cap) -> Should Pass
        res1 = self.crs.register_courses("STU02", ["AI", "DBMS"])
        self.assertIn("Success", res1)
        
        # FIX: Temporarily add a heavy 5-credit course to the catalog to break the 12-credit limit boundary cleanly
        self.crs.catalog["HeavyCourse"] = {"credits": 5, "prereq": None, "capacity": 30, "slots": ["Fri 15:00"], "enrolled": 0}
        
        # 8 credits + 5 credits = 13 credits (Over 12 cap) -> Will trigger Credit limit exceeded
        res2 = self.crs.register_courses("STU02", ["HeavyCourse"])
        self.assertEqual(res2, "Error: Credit limit exceeded")

    def test_timetable_conflict(self):
        # DBMS and ML both run on "Mon 09:00"
        self.crs.students["STU02"]["completed"].append("Programming")
        self.crs.register_courses("STU02", ["DBMS"])
        res = self.crs.register_courses("STU02", ["ML"])
        self.assertIn("Timetable conflict detected for ML", res)

    def test_full_course(self):
        # Artificially fill the class to mimic real-world limits
        self.crs.catalog["DBMS"]["enrolled"] = 60
        res = self.crs.register_courses("STU01", ["DBMS"])
        self.assertIn("is full", res)

    def test_duplicate_registration(self):
        self.crs.register_courses("STU01", ["DBMS"])
        res = self.crs.register_courses("STU01", ["DBMS"])
        self.assertIn("Already registered for DBMS", res)

    def test_invalid_course(self):
        res = self.crs.register_courses("STU01", ["GHOST_COURSE_101"])
        self.assertIn("does not exist", res)

    def test_invalid_student_or_semester_restriction(self):
        res = self.crs.register_courses("FAKE_STUDENT", ["DBMS"])
        self.assertEqual(res, "Invalid Student")

if __name__ == "__main__":
    unittest.main()
