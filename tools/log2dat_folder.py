import pandas as pd
import argparse as argp
from collections import defaultdict as dd
import os

def number_duplicates(data):
    counts = dd(int)
    result = []
    for item in data:
        counts[item] += 1
        if counts[item] > 1:
            result.append(f"{item}{counts[item] - 1}")
        else:
            result.append(item)
    return result

def main(args):
    folder_path = args.input_folder 
    print(folder_path)
    try:
        for filename in os.listdir(folder_path):
            file_path = os.path.join(folder_path, filename)
            if os.path.isfile(file_path):  # Ensure it's a file, not a subdirectory
                try:
                    with open(file_path, 'r') as file:
                        print(f"Opened and processing: {filename}")
                        header_line = file.readline().strip()
                        columns = [segment.split('|')[0].strip('"') for segment in header_line.split(',')]

                    columns = number_duplicates(columns)

                    df = pd.read_csv(file_path, skiprows=1, names=columns, delimiter=',', na_values=['', ' '], on_bad_lines='warn')

                    print(df.head())
                    if args.output_folder is not None:
                        if str.endswith(args.output_type, "csv"):
                            df.to_csv(os.path.join(args.output_folder, filename.replace('.log', '.csv')))
                        elif str.endswith(args.output_type, "xlsx"):
                            df.to_excel(os.path.join(args.output_folder, filename.replace('.log', '.csv')))
                        else: raise TypeError("Output type must be type .xlsx or .csv")
                except Exception as e:
                    print(f"Error opening {filename}: {e}")
    except FileNotFoundError:
      print(f"Error: Folder not found: {folder_path}")
    except Exception as e:
      print(f"An error occurred: {e}")

if __name__ == "__main__":
    parser = argp.ArgumentParser(description="Process log data from an folder file")
    parser.add_argument("-i", "--input_folder", required=True, help = "Path to the input folder")
    parser.add_argument("-o", "--output_folder", required=False, default = None, help = "Path to the output folder")
    parser.add_argument("-t", "--output_type", required=False, default = 'csv', help = "output file type", choices = ['csv','xlsx'])
    args = parser.parse_args()
    main(args)
