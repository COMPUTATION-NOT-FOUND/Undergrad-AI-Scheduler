from exctractor import get_courses

class User:
    def __init__(self, Erp_id, program, credits, courses):
        self.Erp_id = Erp_id
        self.program = program
        self.credits = credits
        self.courses = courses
        self.enrolled_courses = []

    def enroll(self, course):
        # Check if user is not enrolled in this course and if there's no clash
        if course not in self.enrolled_courses:
            # Check for clash (based on the course timing)
            for enrolled_course in self.enrolled_courses:
                if enrolled_course[0] == course[0]:  # Compare course names
                 if enrolled_course[0] & enrolled_course[6] == course[0] & course [6]:  # Compare times of the courses
                    print(f"Conflict with course {enrolled_course[0]} at {enrolled_course[1]}")
                    return False
            self.enrolled_courses.append(course)
            print(f"Successfully enrolled in course {course[0]} at {course[1]}")
            return True
        else:
            print(f"Already enrolled in {course[0]} at {course[1]}")
            return False

class Users:
    users_list = []

    def check_user(self, Erp_id):
        for user in self.users_list:
            if user.Erp_id == Erp_id:
                return True
        return False

    def add_user(self, Erp_id, program, credits, extractor):
        if not self.check_user(Erp_id):
            # Get courses for the user from extractor
            courses = extractor.get_courses(program)  # Using extractor's get_courses
            new_user = User(Erp_id, program, credits, courses)
            self.users_list.append(new_user)
            print(f"User {Erp_id} added to the system.")
        else:
            print(f"User {Erp_id} already exists.")

    def get_user(self, Erp_id):
        for user in self.users_list:
            if user.Erp_id == Erp_id:
                return user
        return None
