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
        infilename = args.file
        tempfilename = os.path.join(os.path.dirname(args.file),'temp.csv')
        if DEBUG: print('cleaning ' + infilename + ' to tmp file ' + tempfilename)
        with open (infilename, 'r') as f, open (tempfilename, 'w') as out:
            writer = csv.writer(out)
            reader = csv.reader(f)
            next (reader,None)
            for row in reader:
                if os.path.exists(os.path.join(os.path.dirname(args.file),row[2])):
                    writer.writerow(row) # only write rows with existing files
                else:
                    if DEBUG: print ('deleting references to file ' + row[2])
    except OSError:
        print(OSError)

    try:
        if DEBUG: print('renaming ' + tempfilename + ' to ' + infilename)
        os.rename(tempfilename,infilename)
    except OSError:
        print('Error renaming file')
        print(OSError)


if __name__ == '__main__':
    clean_csv()