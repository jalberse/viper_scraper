import os
import csv

DEBUG = 1

def clean_csv():
    """
    Removes rows of csv which reference a file which no longer exists
    """
    try:
        with open ('./data/data.csv', 'r') as f, open ('./data/data_tmp.csv', 'w') as out:
            writer = csv.writer(out)
            reader = csv.reader(f)
            next (reader,None)
            for row in reader:
                if os.path.exists(row[2]):
                    writer.writerow(row) # only write rows with existing files
                else:
                    if DEBUG: print ('deleting references to file ' + row[2])
        os.rename('./data/data_tmp.csv','./data/data.csv')
    except OSError:
        print(OSError)


if __name__ == '__main__':
    clean_csv()