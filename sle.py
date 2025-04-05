import os
import re
import pandas as pd
from collections import defaultdict
from datetime import datetime

# ------------------- CONFIGURATION ------------------- #
input_folder = "textfiles//"
part1_output_folder = "sheets//"

if not os.path.exists(part1_output_folder):
    os.makedirs(part1_output_folder)

# ------------------- VALUE PATTERN ------------------- #
value_pattern = r"(\<?\>?[\d\.]+(?:\s*[HL])?)"

# ------------------- TEST PATTERNS ------------------- #
patterns = {
    # Existing tests
    "Blood Creatinine": fr"Creatinine\s+{value_pattern}\s+(?:mmol/L|umol/L)",
    "Urine Creatinine": fr"Urine\s+creatinine\s+{value_pattern}\s+mmol/L",
    "Calcium": fr"Calcium\s+{value_pattern}\s+mmol/L",
    "Urea": fr"Urea\s+{value_pattern}\s+mmol/L",
    "Sodium": fr"Sodium\s+{value_pattern}\s+mmol/L",
    "ESR": fr"ESR\s+{value_pattern}\s+mm/hr",
    "CRP": fr"C-Reactive\s+protein\s+{value_pattern}\s+mg/L",
    "ALP": fr"Alkaline phosphatase\s*\(ALP\)\s+{value_pattern}\s+U/L",
    "GGT": fr"Gamma-glutamyl transferase\s*\(GGT\)\s+{value_pattern}\s+U/L",
    "AST": fr"Aspartate transaminase\s*\(AST\)\s+{value_pattern}\s+U/L",
    "ALT": fr"Alanine transaminase\s*\(ALT\)\s+{value_pattern}\s+U/L",
    "Complement C3": fr"Complement\s+C3\s+{value_pattern}\s+g/L",
    "Complement C4": fr"Complement\s+C4\s+{value_pattern}\s+g/L",

    # Complex patterns
    "AB2GPEL IgG": r"Anti-beta\s*2\s*glycoprotein-1\s*antibody.*?IgG\s+result\s+(Positive|Negative)\s+Value\s+([\d\.]+)",
    "AB2GPEL IgM": r"Anti-beta\s*2\s*glycoprotein-1\s*antibody.*?IgM\s+Result\s+(Positive|Negative)\s+Value\s+([\d\.]+)",
    "ADNAEL": r"Anti-double\s+stranded\s+DNA\s+antibody.*?IgG\s+Result\s+(Positive|Negative)\s+Value\s+([\d\.]+)",
    "ANAIF_Positive": r"Anti-nuclear\s+antibodies.*?\b(Positive)\s+Titre\s+([\d\.]+)",
    "ANAIF_Negative": r"Anti-nuclear\s+antibodies.*?\b(Negative)(?!.*Titre)",

    # New tests:
    "Cholesterol": fr"Cholesterol\s+{value_pattern}\s+mmol/L",
    "HbA1c": fr"HbA1c\s+{value_pattern}\s*%",
    "TSH": fr"TSH\s+{value_pattern}\s+mIU/L",
    "eGFR": fr"eGFR\s+{value_pattern}\s+mL/min/1\.73\s*m2",
    "MCV": fr"MCV\s+{value_pattern}\s+fL",
    "Hb": fr"\bHb\b\s+{value_pattern}\s+g/L",

    # HIV and ACCP patterns
    "HIV Serology": r"HIV\s+(?:antibody\s+test:|status:)\s+(Positive|Negative)",
    "HIV Viral Load": r"HIV\s+Viral\s+Load\s+(\<?\>?[\d\.]+)\s+copies/mL",
    "ACCP": r"Anti-CCP\s+antibod(?:y|ies).*?(Positive|Negative)\s+Value\s+([\d\.]+)\s+U/mL",

    # Hep B markers
    "Hep B": r"(HBsAg|Anti-HBs|Anti-HBc(?:\s+IgM)?|HBeAg|Anti-HBe)\s*:\s*(Positive|Negative|\<?\>?[\d\.]+(?:\s*[HL])?\s*(?:IU/mL)?)",

    # RF
    "RF": fr"Rheumatoid\s+factor\s*\(RF\)\s+{value_pattern}\s+IU/mL",
}


def extract_results_from_lines(lines):
    results = defaultdict(dict)
    current_date = None

    # Regex for capturing date lines
    date_line_pattern = re.compile(r"Date\s+collected\s+(\d{2}/\d{2}/\d{4})")
    print("Starting line-by-line extraction...")

    for line_number, line in enumerate(lines, start=1):
        line = line.strip()
        if not line:
            continue

        # Check if this line contains a date
        date_match = date_line_pattern.search(line)
        if date_match:
            current_date = date_match.group(1)
            print(f"Found date on line {line_number}: {current_date}")
            continue

        if current_date is None:
            # We haven't encountered a date yet, skip
            continue

        # Apply each pattern to the current line
        for test, pattern in patterns.items():
            matches = re.findall(pattern, line, flags=re.DOTALL | re.IGNORECASE)
            if matches:
                print(f"Matches found for '{test}' on line {line_number}: {matches}")
                for match in matches:
                    value_str = None
                    test_name = test

                    if test in ("AB2GPEL IgG", "AB2GPEL IgM", "ADNAEL"):
                        status, val = match
                        if test == "AB2GPEL IgG":
                            value_str = f"IgG {status} - {val}"
                        elif test == "AB2GPEL IgM":
                            value_str = f"IgM {status} - {val}"
                        else:  # ADNAEL
                            value_str = f"IgG {status} - {val}"

                    elif test == "ANAIF_Positive":
                        # match = (Positive, titre)
                        _, titre = match
                        value_str = f"Positive - {titre}"
                        test_name = "ANAIF"
                    elif test == "ANAIF_Negative":
                        # match = ("Negative",)
                        value_str = "Negative"
                        test_name = "ANAIF"
                    elif test == "ACCP":
                        status, val = match
                        value_str = f"{status} - {val}"
                    elif test == "HIV Serology":
                        # match = (Positive|Negative,)
                        status = match
                        value_str = status
                    elif test == "Hep B":
                        # match = (Marker, Result)
                        marker, raw_result = match
                        test_name = marker.strip()

                        if "Positive" in raw_result or "Negative" in raw_result:
                            value_str = raw_result.strip()
                        else:
                            # Remove IU/mL if present and trim
                            val_clean = re.sub(r'\s*IU/mL', '', raw_result).strip()
                            value_str = val_clean
                    else:
                        # For regular numeric tests
                        if isinstance(match, tuple):
                            first_val = match[0] if len(match) > 0 else match
                            value_str = first_val.strip()
                        else:
                            value_str = match.strip()

                    if value_str is not None:
                        print(f"Storing result for {test_name} on {current_date}: {value_str}")
                        results[test_name][current_date] = value_str

    return results

def consolidate_results(all_results):
    print("Consolidating results into DataFrame...")
    # Collect all dates
    all_dates = set()
    for test_name, date_results in all_results.items():
        all_dates.update(date_results.keys())

    # Sort dates chronologically
    all_dates = sorted(all_dates, key=lambda x: pd.to_datetime(x, format='%d/%m/%Y'))
    formatted_dates = [pd.to_datetime(d, dayfirst=True).strftime('%Y-%m-%d') for d in all_dates]

    df = pd.DataFrame(index=all_results.keys(), columns=formatted_dates)
    for test_name, date_values in all_results.items():
        for d, val in date_values.items():
            fd = pd.to_datetime(d, dayfirst=True).strftime('%Y-%m-%d')
            df.at[test_name, fd] = val

    df = df.fillna('-')
    return df

def process_text_files(input_folder, output_folder):
    print("Starting Extraction...")
    for filename in os.listdir(input_folder):
        if filename.endswith('.txt'):
            filepath = os.path.join(input_folder, filename)
            print(f"Processing file: {filename}")
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as file:
                lines = file.readlines()

            results = extract_results_from_lines(lines)
            if not results:
                print(f"No matching results found in {filename}.")
                continue

            df = consolidate_results(results)
            patient_id = os.path.splitext(filename)[0]
            output_file = os.path.join(output_folder, f"{patient_id}.xlsx")
            print(f"Saving extracted results for '{patient_id}' to {output_file}")

            with pd.ExcelWriter(output_file, date_format='yyyy-mm-dd', datetime_format='yyyy-mm-dd') as writer:
                df.to_excel(writer, sheet_name=patient_id[:31], index=True)

    print("Extraction Completed.")

if __name__ == "__main__":
    process_text_files(input_folder, part1_output_folder)
    print("Check the full_output folder for results.")
