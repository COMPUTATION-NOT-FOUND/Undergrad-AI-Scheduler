import csv

class TableExtractor:
    def __init__(self, program, timings, filepath, exception):
        self.program = program
        self.filepath = filepath
        self.days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
        self.timings = timings
        self.exception = exception  # Columns to ignore
        self.headers = []  # Will be filled from CSV header
        self.tables = [[[] for _ in self.days] for _ in self.timings]  # 3D table

    def extract_table(self):
        try:
            with open(self.filepath, newline='', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                self.headers = [h for h in reader.fieldnames if h not in self.exception]

                for row in reader:
                    if row.get("Program", "").strip() != self.program:
                        continue

                    time = row.get("Class Timing", "").strip()
                    day = row.get("Day", "").strip()

                    if time not in self.timings or day not in self.days:
                        continue

                    row_index = self.timings.index(time)
                    col_index = self.days.index(day)

                    class_string = ', '.join(f"{key}: {row[key]}" for key in self.headers if key in row)
                    self.tables[row_index][col_index].append(class_string)

        except FileNotFoundError:
            print(f"❌ File '{self.filepath}' not found.")
        except Exception as e:
            print(f"❌ Error reading file: {e}")

    def display_table(self):
        print(f"\n📅 Timetable for program: {self.program}")
        for i, time in enumerate(self.timings):
            print(f"\n⏰ Time Slot: {time}")
            for j, day in enumerate(self.days):
                entries = self.tables[i][j]
                if entries:
                    print(f"  📍 {day}:")
                    for cls in entries:
                        print(f"    - {cls}")

# test script 
if __name__ == "__main__":
    program = "BSCS-4"
    timings = [
        "8:30 am to 9:45 am",
        "10:00 am to 11:15 am",
        "11:30 am to 12:45 pm",
        "01:00 pm to 2:15 pm",
        "2:30 pm to 3:45 pm",
        "4:00 pm to 5:15 pm",
        "5:30 pm to 6:45 pm"
    ]
    filepath = r"D:\OneDrive\Documents\IBA\GitHub\AI-PROJECT\Cleaned_Schedule\class_schedule_BSCS-4.csv"
    exception = ["Comments"]

    extractor = TableExtractor(program, timings, filepath, exception)
    extractor.extract_table()
    extractor.display_table()
