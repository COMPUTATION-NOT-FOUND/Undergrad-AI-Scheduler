import pandas as pd

# Load the Excel file
df = pd.read_excel("Spring Schedule 2025.xlsx", header=4)

# Print the first few rows of the DataFrame to inspect its structure
print("DataFrame Head:")
print(df.head())

# Define the column positions for each day group
mw_cols = [0, 1, 2, 3, 4, 5]  # Monday/Wednesday
tt_cols = [0, 7, 8, 9, 10, 11]  # Tuesday/Thursday
fs_cols = [0, 12, 13, 14, 15, 16]  # Friday/Saturday

def extract_day_section(df, cols, day_name):
    section = df.iloc[2:, cols].copy()
    section.columns = ['Timing', 'Course Name', 'Class & Program', 'Room No.', 'UMS ClassNo.', 'Teacher']
    section['Day'] = day_name
    section['Timing'] = section['Timing'].ffill()  # Fill missing timings using ffill
    section.dropna(subset=['Course Name'], inplace=True)  # Drop empty rows
    return section[section['Class & Program'] == 'BSCS-4']

# Extract filtered data for each day
mw_bscs4 = extract_day_section(df, mw_cols, "Monday/Wednesday")
tt_bscs4 = extract_day_section(df, tt_cols, "Tuesday/Thursday")
fs_bscs4 = extract_day_section(df, fs_cols, "Friday/Saturday")

# Check if any data was extracted for each day
print(f"Monday/Wednesday courses: {len(mw_bscs4)}")
print(f"Tuesday/Thursday courses: {len(tt_bscs4)}")
print(f"Friday/Saturday courses: {len(fs_bscs4)}")

# Combine all extracted data into a single DataFrame
combined_bscs4 = pd.concat([mw_bscs4, tt_bscs4, fs_bscs4], ignore_index=True)

# Save to Excel if there is any data
if not combined_bscs4.empty:
    with pd.ExcelWriter("BSCS4_Spring_Schedule_All_Days5.xlsx") as writer:
        combined_bscs4.to_excel(writer, sheet_name="BSCS-4 Courses", index=False)
    print("✅ BSCS-4 schedule extracted successfully for all days!")
else:
    print("⚠️ No courses found for BSCS-4.")