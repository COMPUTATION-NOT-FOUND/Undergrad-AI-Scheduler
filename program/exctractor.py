# import csv
# import os
# import sys
import csv
import os
import sys
import json

import json
from typing import List, Any, Dict
from rich.table import Table
from rich.console import Console

# sys.path.append(os.path.join(os.getcwd(), '..'))



# class course:
#     def __init__(self, name, program, instructor, id, room, day, time, comments):
#         self.name = name
#         self.program = program
#         self.instructor = instructor
#         self.id = id
#         self.room = room
#         self.day = day
#         self.time = time
#         self.comments = comments




# class TableExtractor:
#     def __init__(self, program, timings, filepath, exception):
#         self.program = program
#         self.filepath = filepath
#         self.days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
#         self.timings = timings
#         self.exception = exception  # Columns to ignore
#         self.headers = []  # Will be filled from CSV header
#         self.tables = [[[] for _ in self.days] for _ in self.timings]  # 3D table

#     # def extract_table(self):
#     #     try:
#     #         with open(self.filepath, newline='', encoding='utf-8') as csvfile:
#     #             reader = csv.DictReader(csvfile)
#     #             self.headers = [h for h in reader.fieldnames if h not in self.exception]

#     #             for row in reader:
#     #                 if row.get("Program", "").strip() != self.program:
#     #                     continue

#     #                 time = row.get("Class Timing", "").strip()
#     #                 day = row.get("Day", "").strip()

#     #                 if time not in self.timings or day not in self.days:
#     #                     continue

#     #                 row_index = self.timings.index(time)
#     #                 col_index = self.days.index(day)

#     #                 class_string = ', '.join(f"{key}: {row[key]}" for key in self.headers if key in row)
#     #                 self.tables[row_index][col_index].append(class_string)

#     #     except FileNotFoundError:
#     #         print(f"❌ File '{self.filepath}' not found.")
#     #     except Exception as e:
#     #         print(f"❌ Error reading file: {e}")





#     # def display_table(self):
#     #     print(f"\n📅 Timetable for program: {self.program}")
#     #     for i, time in enumerate(self.timings):
#     #         print(f"\n⏰ Time Slot: {time}")
#     #         for j, day in enumerate(self.days):
#     #             entries = self.tables[i][j]
#     #             if entries:
#     #                 print(f"  📍 {day}:")
#     #                 for cls in entries:
#     #                     print(f"    - {cls}")






#     def extract_table(self):
#         try:
#             with open(self.filepath, newline='', encoding='utf-8') as csvfile:
#                 reader = csv.DictReader(csvfile)
#                 self.headers = [h for h in reader.fieldnames if h not in self.exception]

#                 for row in reader:
#                     if row.get("Program", "").strip() != self.program:
#                         continue

#                     time = row.get("Class Timing", "").strip()
#                     day = row.get("Day", "").strip()

#                     if time not in self.timings or day not in self.days:
#                         continue

#                     row_index = self.timings.index(time)
#                     col_index = self.days.index(day)

#                     class_tuple = tuple(row[key] for key in self.headers if key in row)
#                     self.tables[row_index][col_index].append(class_tuple)

#         except FileNotFoundError:
#             print(f"❌ File '{self.filepath}' not found.")
#         except Exception as e:
#             print(f"❌ Error reading file: {e}")


#     def display_table(self):
#         print(f"\n📅 Timetable for program: {self.program}")
#         for i, time in enumerate(self.timings):
#             print(f"\n⏰ Time Slot: {time}")
#             for j, day in enumerate(self.days):
#                 entries = self.tables[i][j]
#                 if entries:
#                     print(f"  📍 {day}:")
#                     for cls in entries:
#                         # Show (key: value) using zip
#                         display = ', '.join(f"{k}: {v}" for k, v in zip(self.headers, cls))
#                         print(f"    - {display}")

# # test script 



#     def get_courses(self, program):
#          self.tables = [[[] for _ in self.days] for _ in self.timings]
#          self.program = program
#          self.extract_table()
#          return self.tables 


# class course:
#     def __init__(self, name: str, program: str, instructor: str, id: str,
#         room: str, day: str, time: str, comments: str) -> None:
#         self.name = name
#         self.program = program
#         self.instructor = instructor
#         self.id = id
#         self.room = room
#         self.day = day
#         self.time = time
#         self.comments = comments

#     def __repr__(self) -> str:
#         return (
#             f"course(name={self.name!r}, program={self.program!r}, instructor={self.instructor!r}, "
#             f"id={self.id!r}, room={self.room!r}, day={self.day!r}, time={self.time!r}, comments={self.comments!r})"
#         )

class Course:
    def __init__(self, name, program, instructor, id, room, day, time, comments):
        self.name = name
        self.program = program
        self.instructor = instructor
        self.id = id
        self.room = room
        self.day = day
        self.time = time  # Expected format: "HH:MM-HH:MM"
        self.comments = comments

    def __str__(self):
        return f"{self.time} | {self.name} | {self.program} | {self.room} | {self.id} | {self.instructor} | {self.day} | {self.comments}"

    def clashes_with(self, other):
        # Clash occurs if same room, same day, and time overlaps
        if self.day != other.day:
            return False

        start1, end1 = self._parse_time(self.time)
        start2, end2 = self._parse_time(other.time)

        # Check if time intervals overlap
        return start1 < end2 and start2 < end1

    def _parse_time(self, time_str):
        # Assumes time format is "HH:MM-HH:MM"
        start_str, end_str = time_str.split("-")
        start = int(start_str.replace(":", ""))
        end = int(end_str.replace(":", ""))
        return start, end

    def __lt__(self, other):
        # Sort by course ID by default
        return self.id < other.id

    def __eq__(self, other):
        return self.id == other.id


class CourseDataLoader:
    """
    Loads a JSON file of courses and returns a list of `course` instances.
    Provides display functionality via rich tables.
    """
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

    def __init__(self, json_path: str) -> None:
        self.json_path = json_path
        self.console = Console()

    def load_courses(self) -> List[Course]:
        with open(self.json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        if not isinstance(data, list):
            raise TypeError(f"Expected JSON array, got {type(data).__name__}")

        courses: List[Course] = []
        for idx, item in enumerate(data):
            if not isinstance(item, dict):
                raise TypeError(f"Item at index {idx} is not an object: {item}")

            validated: Dict[str, Any] = {}
            for field, field_type in self.REQUIRED_FIELDS.items():
                if field not in item:
                    raise KeyError(f"Missing required field '{field}' in item at index {idx}")
                value = item[field]
                if not isinstance(value, field_type):
                    try:
                        value = field_type(value)  # type: ignore
                    except Exception:
                        raise TypeError(
                            f"Field '{field}' at index {idx} expected {field_type.__name__}, got {type(item[field]).__name__}"
                        )
                validated[field] = value

            course_obj = Course(**validated)
            courses.append(course_obj)

        return courses

    def display_schedule(self) -> None:
        """
        Displays a timetable of courses by time slot (rows) and day (columns) using rich.
        Multiple courses in the same slot/day appear as sub-rows.
        """
        courses = self.load_courses()

        # Determine unique days and times
        days_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        days = sorted({c.day.strip() for c in courses}, key=lambda d: days_order.index(d) if d in days_order else len(days_order))
        times = sorted({c.time for c in courses})

        # Build schedule mapping: time -> day -> list of course names
        schedule: Dict[str, Dict[str, List[str]]] = {
            t: {day: [] for day in days} for t in times
        }
        for c in courses:
            schedule[c.time][c.day.strip()].append(c.name)

        # Create table
        table = Table(show_lines=True)
        table.add_column("Time")
        for day in days:
            table.add_column(day)

        # Add rows per time slot, handling multiple courses
        for t in times:
            # find max number of courses in any day for this time
            max_rows = max(len(schedule[t][day]) for day in days)
            for row_idx in range(max_rows if max_rows > 0 else 1):
                row = []
                # Time column on first sub-row, blank on others
                row.append(t if row_idx == 0 else "")
                for day in days:
                    courses_list = schedule[t][day]
                    cell = courses_list[row_idx] if row_idx < len(courses_list) else ""
                    row.append(cell)
                table.add_row(*row)

        self.console.print(table)


if __name__ == "__main__":
    program = "BSCS-4"
    # filepath = r"D:\OneDrive\Documents\IBA\GitHub\AI-PROJECT\Cleaned_Schedule\class_schedule_BSCS-4.csv"
    
    # filepath = "Cleaned_Schedule/class_schedule_BSCS-4.csv"
    
    # exception = ["Comments"]

    # loader = CourseDataLoader("courses.json")
    # loader.display_schedule()

    # # extractor.extract_table()
    # # extractor.display_table()
    c1 = Course('A', 'BSCS', 'B', '1', '2', 'Monday', '08:30-09:30', "Hello")
    c2 = Course('B', 'BSCS', 'C', '1', '5', 'Monday', '08:10-09:30', "Hello")

    print(c1.clashes_with(c2))

