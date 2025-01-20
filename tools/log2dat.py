import pandas as pd
import argparse as argp

def main(args):
    file_path = args.input_file

    with open(file_path, 'r') as file:
        header_line = file.readline().strip()
        columns = [segment.split('|')[0].strip('"') for segment in header_line.split(',')]

    df = pd.read_csv(file_path, skiprows=1, names=columns, delimiter=',', na_values=['', ' '])

    print(df.head())
    if args.output_file is not None:
        if str.endswith(args.output_file, ".csv"):
            df.to_csv(args.output_file)
        elif str.endswith(args.output_file, ".xlsx"):
            df.to_excel(args.output_file)
        else: raise TypeError("Output file must be type .xlsx or .csv")

if __name__ == "__main__":
    parser = argp.ArgumentParser(description="Process log data from an input file")
    parser.add_argument("-i", "--input_file", required=True, help = "Path to the input file")
    parser.add_argument("-o", "--output_file", required=False, default = None, help = "Path to the output file")
    args = parser.parse_args()
    main(args)

