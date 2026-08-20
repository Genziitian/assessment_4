from threading import Lock

class CourseRegistrationSystem:
    def __init__(self, max_credits_default=15):
        # Database setup
        self.catalog = {
            "DBMS": {"credits": 4, "prereq": "Programming", "capacity": 60, "slots": ["Mon 09:00", "Wed 09:00"], "enrolled": 0},
            "AI": {"credits": 4, "prereq": "Data Structures", "capacity": 40, "slots": ["Tue 10:00", "Thu 10:00"], "enrolled": 0},
            "ML": {"credits": 3, "prereq": "Statistics", "capacity": 30, "slots": ["Mon 09:00", "Fri 11:00"], "enrolled": 0}, # Clashes with DBMS
            "Cloud": {"credits": 3, "prereq": "Networking", "capacity": 50, "slots": ["Wed 14:00", "Fri 14:00"], "enrolled": 0}
        }
        # Student database: {student_id: {"completed": [courses], "registered": [courses], "sem": int}}
        self.students = {}
        self.max_credits = max_credits_default
        self.lock = Lock()

    def add_student(self, student_id, completed_courses, current_semester):
        self.students[student_id] = {"completed": completed_courses, "registered": [], "sem": current_semester}

    def register_courses(self, student_id, course_list):
        if student_id not in self.students: return "Invalid Student"
        
        with self.lock:
            student = self.students[student_id]
            current_registered = list(student["registered"])
            total_credits = sum(self.catalog[c]["credits"] for c in current_registered if c in self.catalog)
            occupied_slots = []
            
            # Map slots for already registered courses
            for crs in current_registered:
                occupied_slots.extend(self.catalog[crs]["slots"])

            for course in course_list:
                # 1. Invalid Course Verification
                if course not in self.catalog: return f"Error: {course} does not exist"
                
                info = self.catalog[course]
                
                # 2. Prevent Duplicate Registration
                if course in current_registered: return f"Error: Already registered for {course}"
                
                # 3. Verify Prerequisites
                if info["prereq"] and info["prereq"] not in student["completed"]:
                    return f"Error: Missing prerequisite '{info['prereq']}' for {course}"
                
                # 4. Check Maximum Credit Limits
                if total_credits + info["credits"] > self.max_credits:
                    return "Error: Credit limit exceeded"
                
                # 5. Detect Timetable Clashes
                if any(slot in occupied_slots for slot in info["slots"]):
                    return f"Error: Timetable conflict detected for {course}"
                
                # 6. Check Course Capacity
                if info["enrolled"] >= info["capacity"]:
                    return f"Error: {course} is full"

                # Update running state trackers for validation chain continuity
                total_credits += info["credits"]
                occupied_slots.extend(info["slots"])
                current_registered.append(course)

            # Commitment phase after passing all validation barriers safely
            for course in course_list:
                self.catalog[course]["enrolled"] += 1
                student["registered"].append(course)

            return f"Success: Registered {len(course_list)} courses. Total Credits: {total_credits}"

    def get_registered_credits(self, student_id):
        if student_id not in self.students: return 0
        return sum(self.catalog[c]["credits"] for c in self.students[student_id]["registered"])
