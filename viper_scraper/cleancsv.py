import os
import csv
import argparse

DEBUG = 1

def argument_parsing():
    """
    Parse the arguments

    Returns args
    """

    parser = argparse.ArgumentParser(description="Removes rows of csv which reference a non-existant file")
    parser.add_argument('file', help='The CSV to clean')
    return parser.parse_args()

def clean_csv():
    """
    Removes rows of csv which reference a file which no longer exists
    """
    args = argument_parsing()

    try:
        with open (args.file, 'r') as f, open ('temp.csv', 'w') as out:
            writer = csv.writer(out)
            reader = csv.reader(f)
            next (reader,None)
            for row in reader:
                if os.path.exists(row[2]):
                    writer.writerow(row) # only write rows with existing files
                else:
                    if DEBUG: print ('deleting references to file ' + row[2])
        os.rename('tmp.csv',args.file)
    except OSError:
        print(OSError)


if __name__ == '__main__':
    clean_csv()