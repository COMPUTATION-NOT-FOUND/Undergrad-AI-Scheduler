from flask import Flask, render_template, request, session, redirect, url_for
import json
import pandas as pd
from typing import List, Dict
from collections import defaultdict
from datetime import datetime
import ast
from ac3 import AC3 
from pso import BinaryPSO



app = Flask(__name__)
app.secret_key = "super secret key"  # Required for using sessions





class Course:
    def __init__(self, name, program, instructor, id, room, day, time, comments):
        self.name = name
        self.program = program
        self.instructor = instructor
        self.id = id
        self.room = room
        self.day = day
        self.time = time
        self.comments = comments

    def __str__(self):
        return f"{self.name} - {self.instructor} - {self.id} | {self.time} | {self.day} | Room: {self.room}"

    def to_dict(self):
        return {
            'name': self.name,
            'program': self.program,
            'instructor': self.instructor,
            'id': self.id,
            'room': self.room,
            'day': self.day,
            'time': self.time,
            'comments': self.comments
        }

    @staticmethod
    def from_dict(data):
        return Course(**data)

    def __eq__(self, other):
        return isinstance(other, Course) and self.id == other.id and self.day == other.day and self.time == other.time

    def __hash__(self):
        return hash((self.id, self.day, self.time))

class CourseDataLoader:
    REQUIRED_FIELDS = {
        'name': str,
        'program': str,
        'instructor': str,
        'id': str,
        'room': str,
        'day': str,
        'time': str,
        'comments': str
    }

    def __init__(self, json_path):
        self.json_path = json_path

    def load_courses(self) -> List[Course]:
        with open(self.json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        courses = []
        for idx, item in enumerate(data):
            validated = {}
            for field, field_type in self.REQUIRED_FIELDS.items():
                value = item.get(field, "").strip()
                if not isinstance(value, field_type):
                    value = field_type(value)
                if field in ('day', 'time'):
                    value = value.replace(" ", "")
                validated[field] = value
            courses.append(Course(**validated))
        return courses

    def get_available_programs(self):
        return list({course.program for course in self.load_courses()})

    def load_courses_by_program(self, program_name):
        return [course for course in self.load_courses() if course.program == program_name]

    def get_schedule(self, program_name):
        schedule = defaultdict(lambda: defaultdict(list))
        for course in self.load_courses_by_program(program_name):
            schedule[course.time][course.day].append(course)
        return schedule

    def get_highlighted_course_ids(self):
        course_ids = defaultdict(list)
        for course in self.load_courses():
            course_ids[course.id].append(course)
        colors = ["#f0f8ff", "#faebd7", "#98fb98", "#d3d3d3", "#ffb6c1", "#ffcccb"]
        course_colors = {}
        for i, course_id in enumerate(course_ids):
            course_colors[course_id] = colors[i % len(colors)]
        return course_colors

    def get_course_by_id(self, course_id):
        return [course for course in self.load_courses() if course.id == course_id]

    def get_course_id_mapping(self):
        course_id_mapping = defaultdict(list)
        for course in self.load_courses():
            course_id_mapping[course.id].append(course)
        return course_id_mapping 
    
    def get_course_id_constraint_mapping(self):
        from collections import defaultdict


        course_id_constraint_mapping = defaultdict(lambda: {'constraints': [], 'course_name': None})
        course_id_mapping = self.get_course_id_mapping()

        for course_id, courses in course_id_mapping.items():
            for course in courses:
                if course_id_constraint_mapping[course_id]['course_name'] is None:
                    course_id_constraint_mapping[course_id]['course_name'] = course.name

                day = normalize(course.day)
                time = normalize(course.time)
                constraint_key = f"{day} {time}"
                course_id_constraint_mapping[course_id]['constraints'].append(constraint_key)

        return course_id_constraint_mapping
    
    def get_course_name_to_ids_mapping(self):
        """
        Returns a dict mapping each course name to a list of course IDs that share that name.
        """
        name_to_ids = defaultdict(list)
        for course in self.load_courses():
            
            name_to_ids[course.name].append(course.id)
        return name_to_ids
    
    def get_course_id_to_time_mapping(self):

        id_to_time  = defaultdict (list)
        for course in self.load_courses():
            day = normalize(course.day)
            time = normalize(course.time)
            time_key = f"{day} {time}"
            id_to_time[course.id].append(time_key)
        return id_to_time


def normalize(s):
        return " ".join(s.strip().split())

def get_constraints_from_session():
    return [Course.from_dict(c) for c in session.get('constraints', [])]


def save_constraints_to_session(courses: List[Course]):
    session['constraints'] = [c.to_dict() for c in courses]
    session.modified = True
   

def get_no_class_constraints_from_session():
    """
    Returns a list of (day, time) tuples stored in session under 'no_class'.
    """
    return session.get('no_class', [])

def save_no_class_constraints_to_session(no_class_list):
    """
    Persists the list of (day, time) tuples to session['no_class'].
    """
    session['no_class'] = no_class_list
    session.modified = True


from datetime import datetime

def parse_time_slot(time_input):
    """
    Accept either:
      - A string "Day HH-HH" or "Day HH–HH"
      - A list/tuple [Day, start_hour, end_hour]
    Returns (day, start_datetime, end_datetime).
    """
    # Case 1: already a Day/HH-HH string
    if isinstance(time_input, str):
        day, time_range = time_input.strip().split()
        start_str, end_str = time_range.replace('–', '-').split('-')
        start = datetime.strptime(start_str.strip(), '%H')
        end = datetime.strptime(end_str.strip(), '%H')

    # Case 2: list/tuple [Day, start, end]
    elif isinstance(time_input, (list, tuple)) and len(time_input) == 3:
        day = str(time_input[0]).strip()
        start = datetime.strptime(str(time_input[1]).strip(), '%H')
        end   = datetime.strptime(str(time_input[2]).strip(), '%H')

    else:
        raise ValueError(f"Invalid time slot format: {time_input!r}")

    return day, start, end


def check_time_conflict(times1, times2):
    """
    Given two lists of time slots (each slot either a string or [day, start, end]),
    returns True if any slot in times1 overlaps any in times2 on the same day.
    """
    # Parse into canonical (day, start, end) tuples
    slots1 = [parse_time_slot(t) for t in times1]
    slots2 = [parse_time_slot(t) for t in times2]

    # Check pairwise overlap
    for day1, s1, e1 in slots1:
        for day2, s2, e2 in slots2:
            if day1 == day2 and (s1 < e2 and s2 < e1):
                return True

    return False

@app.route('/', methods=['GET', 'POST'])
def index():
    session.clear()
    course_loader = CourseDataLoader('courses.json')
    available_programs = course_loader.get_available_programs()

    if request.method == 'POST':
        if 'program' in request.form:
            program_name = request.form['program']
            session['program_name'] = program_name
            # Redirect to the schedule route after selecting the program
            return redirect(url_for('schedule'))

    return render_template('index.html', available_programs=available_programs)


@app.route('/schedule', methods=['GET', 'POST'])
def schedule():
    program_name = session.get('program_name', None)
    if not program_name:
        # If no program is selected, redirect back to the index page
        return redirect(url_for('index'))

    course_loader = CourseDataLoader('courses.json')
    highlighted_course_ids = course_loader.get_highlighted_course_ids()
    all_courses = course_loader.load_courses()
    # cid_constraints=course_loader.get_course_id_constraint_mapping()
    

    constraints = get_constraints_from_session()
    no_class_constraints = get_no_class_constraints_from_session()

    # Load the schedule for the selected program
    schedule = course_loader.get_schedule(program_name)

    if request.method == 'POST':
        if 'course_id' in request.form:
            course_id = request.form['course_id']
            for c in all_courses:
                if c.id == course_id and c not in constraints:
                    constraints.append(c)
            save_constraints_to_session(constraints)

        if 'remove_course_id' in request.form:
            remove_id = request.form['remove_course_id']
            constraints = [c for c in constraints if c.id != remove_id]
            save_constraints_to_session(constraints)

        if 'no_class_day' in request.form and 'no_class_time' in request.form:
            day = request.form['no_class_day']
            time = request.form['no_class_time']
            if (day, time) not in no_class_constraints:
                no_class_constraints.append((day, time))
                save_no_class_constraints_to_session(no_class_constraints)

        if 'no_class_day_remove' in request.form and 'no_class_time_remove' in request.form:
            rd, rt = request.form['no_class_day_remove'], request.form['no_class_time_remove']
            no_class_constraints = [(d, t) for (d, t) in no_class_constraints if not (d == rd and t == rt)]
            save_no_class_constraints_to_session(no_class_constraints)

      
    return render_template(
        'schedule.html',
        program_name=program_name,
        schedule=schedule,
        highlighted_course_ids=highlighted_course_ids,
        constraints=constraints,
        no_class_constraints=no_class_constraints
    )


@app.route('/clear_constraints', methods=['POST'])
def clear_constraints():
    save_constraints_to_session([])
    return redirect(url_for('schedule'))

@app.route('/clear_no_class_constraints', methods=['POST'])
def clear_no_class_constraints():
    save_no_class_constraints_to_session([])
    return redirect(url_for('schedule'))



@app.route('/make_schedule', methods=['GET', 'POST'])
def make_schedule():
    # Here you can render a form to choose the constraint satisfaction algorithm
    if request.method == 'POST':
        # handle algorithm selection and perform scheduling
        algorithm = request.form.get('algorithm')
        # implement scheduling logic with the selected algorithm
        return redirect(url_for('schedule'))
    
    return render_template('make_schedule.html')

@app.route('/ac3_schedule', methods=['GET','POST'])
def ac3_schedule():
    # Load courses and both kinds of constraints
    course_loader = CourseDataLoader('courses.json')
    session_course_constraints = get_constraints_from_session() 
    session_no_class = get_no_class_constraints_from_session()

    # Initialize AC-3 with no-class constraints, too
    ac3_algo = AC3(
        courses=course_loader.load_courses(),
        cid_constraints=course_loader.get_course_id_constraint_mapping(),
        session_constraints=session_course_constraints,
        no_class_constraints=session_no_class
    )

    # Run and store
    solutions = ac3_algo.solve()
    session['ac3_solutions'] = solutions
    session['ac3_progress'] = ac3_algo.progress

    return redirect(url_for('generated_schedules'))


@app.route('/generated_schedules', methods=['GET'])
def generated_schedules():
    solutions = session.get('ac3_solutions', [])
    progress = session.get('ac3_progress', [])
    all_rows = [] 

    course_loader = CourseDataLoader('courses.json')
    course_id_mapping = course_loader.get_course_id_constraint_mapping()
    idx=0
    schedule_tables = []
    for sol in solutions:
        
        rows = []
        for var, cid in sol.items():
            course_info = course_id_mapping.get(cid)
            if course_info:
                course_name = course_info['course_name']
                constraints = course_info['constraints']
                row = {
                    'id': cid,
                    'name': course_name,
                    'constraints': constraints  # List of "Day Time" strings
                }
                rows.append(row)
        schedule_tables.append(rows)
        # Add to master list for CSV, with a header row for each solution
    #     df = pd.DataFrame(rows)
    #     df.insert(0, 'Solution', f'Solution #{idx + 1}')
    #     all_rows.append(df)

    #     # Add a blank row (gap) between solutions
    #     all_rows.append(pd.DataFrame([[""] * len(df.columns)], columns=df.columns))
    #     idx+=1

    # # Concatenate all into a single DataFrame and save to CSV
    # final_df = pd.concat(all_rows, ignore_index=True)
    # final_df.to_csv("generated_schedules.csv", index=False)

    return render_template('generated_schedules.html',
                           schedule_tables=schedule_tables,
                           progress=progress)





# @app.route('/generated_schedules', methods=['GET'])
# def generated_schedules():
#     solutions = session.get('ac3_solutions', [])
#     progress = session.get('ac3_progress', [])

#     course_loader = CourseDataLoader('courses.json')
#     course_id_mapping = course_loader.get_course_id_constraint_mapping()

#     schedule_tables = []
#     all_rows = []  # To collect rows for CSV

#     for idx, sol in enumerate(solutions):
#         rows = []
#         for var, cid in sol.items():
#             course_info = course_id_mapping.get(cid)
#             if course_info:
#                 course_name = course_info['course_name']
#                 constraints = course_info['constraints']  # List of "Day Time" strings
#                 row = {
#                     'ID': cid,
#                     'Name': course_name,
#                     'Constraints': ", ".join(constraints)
#                 }
#                 rows.append(row)
#         schedule_tables.append(rows)

#         # Add to master list for CSV, with a header row for each solution
#         df = pd.DataFrame(rows)
#         df.insert(0, 'Solution', f'Solution #{idx + 1}')
#         all_rows.append(df)

#         # Add a blank row (gap) between solutions
#         all_rows.append(pd.DataFrame([[""] * len(df.columns)], columns=df.columns))

#     # Concatenate all into a single DataFrame and save to CSV
#     final_df = pd.concat(all_rows, ignore_index=True)
#     final_df.to_csv("generated_schedules.csv", index=False)

#     return render_template('generated_schedules.html',
#                            schedule_tables=schedule_tables,
#                            progress=progress)


@app.route('/pso_schedule', methods=['GET', 'POST'])
def pso_schedule():
    if request.method == 'POST':
        try:
            # 1) Parse numeric and weight inputs
            num_students          = int(request.form['num_students'])
            num_courses           = int(request.form['num_courses'])
            num_particles         = int(request.form['num_particles'])
            max_iterations        = int(request.form['max_iterations'])
            inertia_weight        = float(request.form['inertia_weight'])
            cognitive_coefficient = float(request.form['cognitive_coefficient'])
            social_coefficient    = float(request.form['social_coefficient'])
            preference_weight     = float(request.form['preference_weight'])
            time_weight           = float(request.form['time_weight'])
            label_weight          = float(request.form['label_weight'])
            capacity_weight       = float(request.form['capacity_weight'])
            course_load_weight    = float(request.form['course_load_weight'])
            seed                 =int(request.form['seed'])

            # 2) Parse list‐like inputs
            student_preferences = ast.literal_eval(request.form['student_preferences'])
            course_times         = ast.literal_eval(request.form['course_times'])
            course_caps          = ast.literal_eval(request.form['course_caps'])

            # 3) Robustly parse course labels
            raw_labels = request.form.getlist('course_labels')
            if len(raw_labels) == 1:
                try:
                    parsed = ast.literal_eval(raw_labels[0])
                    course_labels = [str(l).strip() for l in parsed] if isinstance(parsed, list) \
                                    else [l.strip() for l in raw_labels[0].split(',')]
                except:
                    course_labels = [l.strip() for l in raw_labels[0].split(',')]
            else:
                course_labels = [str(l).strip() for l in raw_labels]

            # 4) Validate lengths
            if len(course_labels) != num_courses:
                return render_template('pso_schedule.html', error="Number of course labels must match number of courses.")
            if len(course_caps) != num_courses:
                return render_template('pso_schedule.html', error="Number of course capacities must match number of courses.")
            if len(student_preferences) != num_students:
                return render_template('pso_schedule.html', error="Number of student preference lists must match number of students.")
            if len(course_times) != num_courses:
                return render_template('pso_schedule.html', error="Number of course times must match number of courses.")

            # 5) Run PSO
            pso = BinaryPSO(
                num_students, num_courses, num_particles, max_iterations,
                inertia_weight, cognitive_coefficient, social_coefficient,
                student_preferences, course_times, course_labels, course_caps,
                preference_weight, time_weight, label_weight, capacity_weight,
                course_load_weight, seed
            )
            best_solution, best_fitness = pso.run()
            enrollment_matrix = best_solution.tolist()
            course_names      = [f"Course {i+1}" for i in range(num_courses)]
            student_names     = [f"Student {i+1}" for i in range(num_students)]

            # 6) Build time_conflicts
            time_conflicts = [[[] for _ in range(num_courses)] for _ in range(num_students)]
            for i in range(num_students):
                for c1 in range(num_courses):
                    for c2 in range(c1+1, num_courses):
                        if check_time_conflict(course_times[c1], course_times[c2]):
                            time_conflicts[i][c1].append(c2)
                            time_conflicts[i][c2].append(c1)

            # 7) Precompute violation_matrix with CSS classes
            priority_map = {
                'label':      'bg-red-100',
                'time':       'bg-orange-100',
                'capacity':   'bg-yellow-100',
                'preference': 'bg-blue-100',
                'none':       'bg-green-100'
            }
            # count enrollments per course
            course_counts = [sum(row[j] for row in enrollment_matrix) for j in range(num_courses)]
            violation_matrix = []
            for i in range(num_students):
                # labels for selected courses
                selected = [j for j in range(num_courses) if enrollment_matrix[i][j] == 1]
                label_counts = {}
                for j in selected:
                    lab = course_labels[j]
                    label_counts[lab] = label_counts.get(lab, 0) + 1

                row_classes = []
                for j in range(num_courses):
                    if enrollment_matrix[i][j] == 0:
                        row_classes.append('')  # not enrolled
                        continue

                    vio = set()
                    # preference violation
                    if j not in student_preferences[i]:
                        vio.add('preference')
                    # capacity violation
                    if course_counts[j] > course_caps[j]:
                        vio.add('capacity')
                    # time conflict violation
                    if any(other in time_conflicts[i][j] for other in selected):
                        vio.add('time')
                    # label conflict violation
                    if label_counts.get(course_labels[j], 0) > 1:
                        vio.add('label')

                    # pick highest‐priority violation
                    for key in ('label','time','capacity','preference'):
                        if key in vio:
                            row_classes.append(priority_map[key])
                            break
                    else:
                        row_classes.append(priority_map['none'])

                violation_matrix.append(row_classes)

            # 8) Render with precomputed matrices
            return render_template('pso_results.html',
                enrollment_matrix=enrollment_matrix,
                violation_matrix=violation_matrix,
                course_names=course_names,
                student_names=student_names,
                best_fitness=best_fitness,
                course_labels=course_labels,
                course_caps=course_caps,
                preference_weight=preference_weight,
                time_weight=time_weight,
                label_weight=label_weight,
                capacity_weight=capacity_weight,
                course_load_weight=course_load_weight,
                student_preferences=student_preferences,
                course_times=course_times,
                time_conflicts=time_conflicts
            )

        except Exception as e:
            return render_template('pso_schedule.html', error=f"Invalid input format: {e}")

    # GET method
    return render_template('pso_schedule.html')


@app.route('/algorithm_handler', methods=['POST'])
def algorithm_handler():
    selected_algorithm = request.form['algorithm']
    
    if selected_algorithm == 'ac-3':
        return redirect(url_for('ac3_schedule'))  # Redirect to the AC-3 scheduling page
    elif selected_algorithm == 'pso':
        return redirect(url_for('pso_schedule'))  # Redirect to the PSO scheduling page
    else:
        return redirect(url_for('index'))  # Fallback to the index page if the algorithm is unrecognized


if __name__ == '__main__':
    app.run(debug=True)
