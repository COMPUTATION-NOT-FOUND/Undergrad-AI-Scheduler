import numpy as np
import random

class BinaryPSO:
    def __init__(self, num_students, num_courses, num_particles, max_iterations,
                 inertia_weight, cognitive_coefficient, social_coefficient,
                 student_preferences, course_times, course_labels, course_caps,
                 preference_weight=1, time_weight=3, label_weight=4, capacity_weight=2,
                 course_load_weight=5, seed=None):
        # ——— Seed everything for reproducibility ———
        if seed is not None:
            np.random.seed(seed)
            random.seed(seed)

        self.num_students = num_students
        self.num_courses = num_courses
        self.num_particles = num_particles
        self.max_iterations = max_iterations
        self.inertia_weight = inertia_weight
        self.cognitive_coefficient = cognitive_coefficient
        self.social_coefficient = social_coefficient
        self.student_preferences = student_preferences
        self.course_times = course_times
        self.course_labels = course_labels
        self.course_caps = course_caps
        self.preference_weight = preference_weight
        self.time_weight = time_weight
        self.label_weight = label_weight
        self.capacity_weight = capacity_weight
        self.course_load_weight = course_load_weight
        self.unique_labels = set(course_labels)

        # Initialize positions & velocities
        self.binary_table = np.random.randint(0, 2, 
            (num_particles, num_students, num_courses))
        self.velocities = np.random.uniform(-1, 1, 
            (num_particles, num_students, num_courses))

        # Bests
        self.personal_best_positions = self.binary_table.copy()
        self.global_best_position = self.binary_table[0].copy()
        self.global_best_fitness = float('inf')

    def fitness_function(self, particle):
        preference_clashes = 0
        time_clashes = 0
        label_clashes = 0
        capacity_clashes = 0
        course_load_penalty = 0

        for student_id in range(self.num_students):
            selected_courses = np.where(particle[student_id] == 1)[0]
            student_prefs = self.student_preferences[student_id]
            enrolled_labels = set()

            # Preference & collect labels
            for course_id in selected_courses:
                if course_id not in student_prefs:
                    preference_clashes += 1
                enrolled_labels.add(self.course_labels[course_id])

            # Time clashes
            for i in range(len(selected_courses)):
                for j in range(i+1, len(selected_courses)):
                    times_i = self.course_times[selected_courses[i]]
                    times_j = self.course_times[selected_courses[j]]
                    for day_i, s_i, e_i in times_i:
                        for day_j, s_j, e_j in times_j:
                            if day_i == day_j and (s_i < e_j and e_i > s_j):
                                time_clashes += 1

            # Label clashes
            label_counts = {}
            for cid in selected_courses:
                lab = self.course_labels[cid]
                label_counts[lab] = label_counts.get(lab, 0) + 1
            for count in label_counts.values():
                if count > 1:
                    label_clashes += count - 1

            # Course load penalty
            num_unique = len(enrolled_labels)
            total_unique = len(self.unique_labels)
            if num_unique < total_unique:
                course_load_penalty += (total_unique - num_unique)

        # Capacity clashes
        for cid in range(self.num_courses):
            enrolled = np.sum(particle[:, cid])
            if enrolled > self.course_caps[cid]:
                capacity_clashes += (enrolled - self.course_caps[cid])

        return (
            self.preference_weight * preference_clashes +
            self.time_weight       * time_clashes       +
            self.label_weight      * label_clashes      +
            self.capacity_weight   * capacity_clashes   +
            self.course_load_weight* course_load_penalty
        )

    def update_velocities(self):
        for i in range(self.num_particles):
            for j in range(self.num_students):
                for k in range(self.num_courses):
                    r1 = random.random()
                    r2 = random.random()
                    self.velocities[i,j,k] = (
                        self.inertia_weight  * self.velocities[i,j,k]
                      + self.cognitive_coefficient * r1 * (self.personal_best_positions[i,j,k] - self.binary_table[i,j,k])
                      + self.social_coefficient    * r2 * (self.global_best_position[j,k]       - self.binary_table[i,j,k])
                    )

    def update_positions(self):
        for i in range(self.num_particles):
            for j in range(self.num_students):
                for k in range(self.num_courses):
                    sigmoid = 1 / (1 + np.exp(-self.velocities[i,j,k]))
                    self.binary_table[i,j,k] = 1 if random.random() < sigmoid else 0

    def update_personal_and_global_best(self):
        for i in range(self.num_particles):
            fitness_current = self.fitness_function(self.binary_table[i])
            fitness_personal = self.fitness_function(self.personal_best_positions[i])

            if fitness_current < fitness_personal:
                self.personal_best_positions[i] = self.binary_table[i].copy()

            if fitness_current < self.global_best_fitness:
                self.global_best_fitness = fitness_current
                self.global_best_position = self.binary_table[i].copy()

    def run(self):
        for itr in range(self.max_iterations):
            self.update_velocities()
            self.update_positions()
            self.update_personal_and_global_best()
            print(f"Iter {itr+1}/{self.max_iterations}, Best Fitness: {self.global_best_fitness}")
        return self.global_best_position, self.global_best_fitness

    def get_results(self):
        return self.global_best_position, self.global_best_fitness
