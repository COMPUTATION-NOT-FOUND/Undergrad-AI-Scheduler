import pandas as pd

# Load Excel with header starting from 5th row
df = pd.read_excel("Spring Schedule 2025.xlsx", header=4)

# --- Extract Each Day's Section ---
def extract_section(df, cols, day_label):
    section = df.iloc[2:, cols].copy()
    section.columns = ['Timing', 'Course Name', 'Class & Program', 'Room No.', 'UMS ClassNo.', 'Teacher']
    section['Day'] = day_label
    section['Timing'] = section['Timing'].fillna(method='ffill')
    return section

# Columns for each section
mw = extract_section(df, [0, 1, 2, 3, 4, 5], "Monday/Wednesday")
tt = extract_section(df, [0, 7, 8, 9, 10, 11], "Tuesday/Thursday")
fs = extract_section(df, [0, 12, 13, 14, 15, 16], "Friday/Saturday")

# Combine all sections
full_schedule = pd.concat([mw, tt, fs], ignore_index=True)

# Filter for BSCS-4
bscs4 = full_schedule[full_schedule['Class & Program'] == 'BSCS-4'].copy()

# --- Generate SQL File ---
with open("bscs4_courses.sql", "w", encoding="utf-8") as f:
    for _, row in bscs4.iterrows():
        sql = (
            "INSERT INTO bscs4_courses (day, timing, course_name, room_no, class_code, ums_code, teacher) "
            f"VALUES ('{row['Day']}', '{row['Timing']}', '{row['Course Name']}', "
            f"'{row['Room No.']}', '{row['Class & Program']}', '{row['UMS ClassNo.']}', "
            f"'{row['Teacher']}');\n"
        )
        f.write(sql)

print("✅ SQL file 'bscs4_courses.sql' has been created!")
# Assuming `bscs4` is your filtered DataFrame from earlier

# Reorder and rename columns (keeping the Day at end for clarity)
bscs4_courses = bscs4[['Timing', 'Course Name', 'Class & Program', 'Room No.', 'UMS ClassNo.', 'Teacher', 'Day']]

# Save to new Excel file
bscs4_courses.to_excel("BSCS4_Spring_Schedule.xlsx", index=False)

print("Excel file 'BSCS4_Spring_Schedule.xlsx' has been created.")