import pandas as pd

# Load the Excel file
df = pd.read_excel(r"C:\Users\neera\OneDrive\University\Spring 2025\AI\Project\Data set testing\MW.xlsx")

# Clean column names by stripping extra spaces
df.columns = df.columns.str.strip()

# Print column names for debugging
print("Available columns:", df.columns.tolist())

# Filter data for BSCS-4
if 'Class & Program' in df.columns:
    filtered_df = df[df['Class & Program'] == 'BSCS-4']
else:
    raise KeyError("Column 'Class & Program' not found. Please check column names above.")

# Save as TXT
filtered_df.to_csv("BSCS4_courses_MW1.txt", index=False, sep='\t')

# Save as SQL
with open("BSCS4_courses_MW1.sql", "w", encoding='utf-8') as f:
    for _, row in filtered_df.iterrows():
        sql = f"""INSERT INTO course_schedule 
(Timings, Course_Name, Class_Program, Room_No, UMS_ClassNo, Teacher)
VALUES ('{row['Timings']}', '{row['Course Name']}', '{row['Class & Program']}', 
'{row['Room No.']}', '{row['UMS ClassNo.']}', '{row['Teacher']}');\n"""
        f.write(sql)

# Save as Excel
filtered_df.to_excel("BSCS4_courses_MW1.xlsx", index=False)

print("Data saved to TXT, SQL, and Excel files.")
