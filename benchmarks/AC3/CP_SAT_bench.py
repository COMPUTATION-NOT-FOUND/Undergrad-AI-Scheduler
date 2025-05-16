import pandas as pd
import csv
from ortools.sat.python import cp_model

# Step 1: Load and normalize data
df = pd.read_csv("cleaned_schedule.csv")
df['time'] = df['time'].str.strip()
df['day'] = df['day'].str.strip()
df['id'] = df['id'].astype(str)

# Create unique time slots
df['slot'] = df['day'] + " " + df['time']

# Step 2: Group sessions by course ID (same course with multiple sessions)
course_groups = df.groupby('id')

# Step 3: OR-Tools setup
model = cp_model.CpModel()
course_vars = {cid: model.NewBoolVar(f"course_{cid}") for cid in course_groups.groups}

# === Optional Custom Constraints ===
required_courses = set()  # example required course IDs
banned_courses = set()    # example banned course IDs

# Enforce required courses
for cid in required_courses:
    if cid in course_vars:
        model.Add(course_vars[cid] == 1)

# Enforce banned courses
for cid in banned_courses:
    if cid in course_vars:
        model.Add(course_vars[cid] == 0)

# Step 4: Prevent time slot conflicts
slot_to_course_ids = {}
for course_id, group in course_groups:
    for slot in group['slot'].unique():
        slot_to_course_ids.setdefault(slot, set()).add(course_id)

for slot, course_ids in slot_to_course_ids.items():
    model.Add(sum(course_vars[cid] for cid in course_ids if cid in course_vars) <= 1)

# Step 5: Pick exactly one version of each course name (full course load)
name_to_ids = df.groupby("name")['id'].unique().to_dict()
for name, ids in name_to_ids.items():
    model.Add(sum(course_vars[cid] for cid in ids if cid in course_vars) == 1)

# Step 6: Solution printer class to collect and print all solutions
class SchedulePrinter(cp_model.CpSolverSolutionCallback):
    def __init__(self, course_vars, df, max_solutions=100):
        cp_model.CpSolverSolutionCallback.__init__(self)
        self.course_vars = course_vars
        self.df = df
        self.solutions = []
        self.max_solutions = max_solutions
        self.solution_count = 0

    def on_solution_callback(self):
        selected_ids = [cid for cid, var in self.course_vars.items() if self.Value(var)]
        selected_df = self.df[self.df['id'].isin(selected_ids)].sort_values(['day', 'time'])
        self.solutions.append(selected_df)
        self.solution_count += 1

        print(f"\nSolution #{self.solution_count}:\n")
        print(selected_df[['id', 'day', 'time', 'name', 'room', 'instructor']])

        if self.solution_count >= self.max_solutions:
            self.StopSearch()

# Step 7: Solve and collect all feasible schedules
solver = cp_model.CpSolver()
printer = SchedulePrinter(course_vars, df, max_solutions=10000)  # Adjust max_solutions as needed
solver.SearchForAllSolutions(model, printer)

output_path = "benchmarks/AC3/generated_schedules.csv"

# helper for chronological sort
DAY_ORDER = {
    'Monday':    1,
    'Tuesday':   2,
    'Wednesday': 3,
    'Thursday':  4,
    'Friday':    5,
    'Saturday':  6,
    'Sunday':    7
}
def slot_key(slot: str):
    # slot is like "Tuesday 14:30-15:45"
    day, times = slot.split(' ', 1)
    start, _ = times.split('-', 1)
    h, m = map(int, start.split(':'))
    return DAY_ORDER.get(day, 0), h*60 + m

if printer.solutions:
    with open(output_path, "w", newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["Solution","id","name","constraints"])

        for i, sol in enumerate(printer.solutions):
            # group sessions by course ID
            grouped = sol.groupby('id').agg({
                'name': 'first',
                'slot': lambda slots: sorted(slots, key=slot_key)
            }).reset_index()

            # write each course row in ascending course‐ID order
            for _, row in grouped.sort_values('id').iterrows():
                writer.writerow([
                    f"Solution #{i + 1}",
                    row['id'],
                    row['name'],
                    str(row['slot'])
                ])

            # blank separator
            writer.writerow(["", "", "", ""])

    print(f"\nSaved {len(printer.solutions)} formatted solutions to {output_path}")
else:
    print("No solutions found.")