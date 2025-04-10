import pandas as pd

# Load Excel with header at 5th row
df = pd.read_excel("Spring Schedule 2025.xlsx", header=4)

def extract_section(df, cols, day_label):
    section = df.iloc[2:, cols].copy()
    section.columns = ['Timing', 'Course Name', 'Class & Program', 'Room No.', 'UMS ClassNo.', 'Teacher']
    section['Day'] = day_label
    section['Timing'] = section['Timing'].fillna(method='ffill')
    return section

# Extract sections
mw = extract_section(df, [0, 1, 2, 3, 4, 5], "Monday/Wednesday")
tt = extract_section(df, [0, 7, 8, 9, 10, 11], "Tuesday/Thursday")
fs = extract_section(df, [0, 12, 13, 14, 15, 16], "Friday/Saturday")

# Filter for BSCS-4
mw_bscs4 = mw[mw['Class & Program'] == 'BSCS-4']
tt_bscs4 = tt[tt['Class & Program'] == 'BSCS-4']
fs_bscs4 = fs[fs['Class & Program'] == 'BSCS-4']

# Save each day’s data to a separate Excel sheet
with pd.ExcelWriter("BSCS4_Spring_Schedule 2.xlsx") as writer:
    mw_bscs4.to_excel(writer, sheet_name='Mon_Wed', index=False)
    tt_bscs4.to_excel(writer, sheet_name='Tue_Thu', index=False)
    fs_bscs4.to_excel(writer, sheet_name='Fri_Sat', index=False)

print("Excel file with BSCS-4 courses by day created!")
