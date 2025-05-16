import csv
import json

# Input and output file names
input_file = "cleaned_schedule.csv"
output_file = "courses.json"

# Read CSV and convert to JSON
def convert_csv_to_json(csv_filename, json_filename):
    with open(csv_filename, mode='r', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        data = list(reader)

    with open(json_filename, mode='w', encoding='utf-8') as jsonfile:
        json.dump(data, jsonfile, indent=4)

if __name__ == "__main__":
    convert_csv_to_json(input_file, output_file)
