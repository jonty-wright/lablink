import pandas as pd
import re
from datetime import datetime
import os
# Full Blood Count Parsing Function
def parse_fbc_section(text_section):
    date_line = re.search(r"Date Collected\s+([\d\/\s]+)", text_section)
    if not date_line:
        return None, None
    dates = re.findall(r"\d{2}/\d{2}/\d{4}", date_line.group(1))
    
    results_dict = {}
    test_lines = text_section.strip().split('\n')[1:]  # Skip date line
    for line in test_lines:
        if line.strip():
            parts = line.split('\t')
            test_name = parts[0].strip().replace('Cou', 'Count')
            results = parts[1:]
            results_dict[test_name] = results
    return dates, results_dict

def consolidate_fbc_data(text):
    fbc_tests = {"White Cell Count", "Red Cell Count", "Haemoglobin", 
                 "Haematocrit", "MCH", "MCV", "Platelet Count"}  # Ensure Platelet Count and Red Cell Count are included
    sections = text.split("Date Collected\t")[1:]
    full_data = {}
    for section in sections:
        dates, results_dict = parse_fbc_section("Date Collected\t" + section)
        if not dates:
            continue
        for test_name, results in results_dict.items():
            if test_name in fbc_tests:
                for date, result in zip(dates, results):
                    date_key = datetime.strptime(date, '%d/%m/%Y').date()
                    full_data.setdefault(test_name, {}).setdefault(date_key, []).append(result)

    return pd.DataFrame(full_data)

# Chemistry and Histopathology Results Parsing Function
def parse_lab_results(text):
    episodes = re.split(r'Episode\s+\w+', text)[1:]
    results = {}
    for episode in episodes:
        date_match = re.search(r'Date collected\s+(\d{2}/\d{2}/\d{4})', episode)
        if not date_match:
            continue
        date = datetime.strptime(date_match.group(1), '%d/%m/%Y').date()
        tests = {
        "Urine protein": r"Urine protein\s+([\d.]+)?\s*g/L",
        "Urine protein creat ratio": r"Urine protein\s+creat ratio\s+([\d.]+)?\s*H?\s*g/mmol creat",
        "Creatinine": r"Creatinine\s+(\d+)\s*L?\s*umol/L",
        "Sodium": r"Sodium\s+(\d+)\s*mmol/L",
        "Urea": r"Urea\s+([\d.]+)\s+mmol/L",
        "Calcium": r"Calcium\s+([\d.]+)\s+mmol/L",        
        "Histopathology": r"CLINICAL:(.*?)(?=PATHOLOGIST:)",
        "LA": r"Lupus Anticoagulant:.*?Normalised LAC Ratio\s+([\d.]+\s*[A-Za-z]?)",
        # "Neutrophils %": r"Neutrophils %\n(\d+\.\d+)",
        # "Neutrophils": r"Neutrophils\n(\d+\.\d+)\n",
        # "Lymphocytes %": r"Lymphocytes %\n(\d+\.\d+)",
        # "Lymphocytes": r"Lymphocytes\n(\d+\.\d+)\n",
        # "Monocytes %": r"Monocytes %\n(\d+\.\d+)",
        # "Monocytes": r"Monocytes\n(\d+\.\d+)\n",
        # "Eosinophils %": r"Eosinophils %\n(\d+\.\d+)",
        # "Eosinophils": r"Eosinophils\n(\d+\.\d+)\n",
        # "Basophils %": r"Basophils %\n(\d+\.\d+)",
        # "Basophils": r"Basophils\n(\d+\.\d+)\n",
        # "Immature Cells %": r"Immature Cells %\n(\d+\.\d+)",
        # "Immature Cells": r"Immature Cells\n(\d+\.\d+)\n"
    }



        results.setdefault(date, {test: '-' for test in tests})
        for test, pattern in tests.items():
            match = re.search(pattern, episode, re.DOTALL)
            if match:
                result_value = match.group(1).strip() if test in ["Histopathology", "LA"] else f"{match.group(1)} - {match.group(2)}" if len(match.groups()) > 1 else match.group(1)
                results[date][test] = result_value
    return pd.DataFrame.from_dict(results, orient='index')



def translate (text_content,id):
    
    # Get DataFrames from both functions
    fbc_df = consolidate_fbc_data(text_content)
    chem_df = parse_lab_results(text_content)

    # Combine the dataframes
    combined_df = pd.concat([fbc_df, chem_df], axis=1).sort_index()

    # Convert index to datetime objects
    combined_df.index = pd.to_datetime(combined_df.index, format='%Y-%m-%d').date

    # Since you want to remove list handling for cleaner data access, here's a more straightforward approach:
    for col in combined_df.columns:
        combined_df[col] = combined_df[col].apply(lambda x: x[0] if isinstance(x, list) and x != ['-'] else x)

    # Transpose the DataFrame so that columns become rows and vice versa
    combined_df = combined_df.transpose()
    # print(combined_df)

    # Now save the transposed DataFrame to Excel
    output_file_path = 'output sheets\\' + str(id) + '.xlsx'
    with pd.ExcelWriter(output_file_path, date_format='yyyy-mm-dd', datetime_format='yyyy-mm-dd') as writer:
        combined_df.to_excel(writer, index_label='Test/Date')

    print(f"Excel file saved: {output_file_path}")

def process_files_in_folder(folder_path):
    """
    Process all .txt files in the given folder by running the translate function on each file.

    Args:
        folder_path (str): Path to the folder containing .txt files.
    """
    try:
        for file_name in os.listdir(folder_path):
            if file_name.endswith(".txt"):
                # Extract file name without extension
                file_base_name = os.path.splitext(file_name)[0]

                # Read the file content
                file_path = os.path.join(folder_path, file_name)
                with open(file_path, 'r', encoding='utf-8') as file:
                    content = file.read()
                    # print(content)
                    print(file_path)

                # Run the translate function
                translate(content, file_base_name)
    except Exception as e:
        print("Hello")
        # print(f"An error occurred: {e}")


# Example usage
if __name__ == "__main__":
    folder_path = "output files"  # Replace with the path to your folder
    process_files_in_folder(folder_path)