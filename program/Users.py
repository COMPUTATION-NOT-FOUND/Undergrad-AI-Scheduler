from exctractor import get_courses

class user:
    def _init_(self, Erp_id, program , credits , courses):
        self.Erp_id = Erp_id
        self.program = program
        self.credits = credits
        self.courses = []
    
class users(user):
    users_list = []
    def check_user(self, Erp_id):
        for user in self.users_list:
            if user.Erp_id == Erp_id:
                return True
        return False
    def add_user(self, user):
        if not self.check_user(user.Erp_id):
            self.users_list.append(user) 
    def get_user(self, Erp_id):
        for user in self.users_list:
            if user.Erp_id == Erp_id:
                return user
        return None