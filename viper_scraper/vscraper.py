import argparse
import string
import sys
import time
from datetime import datetime

from viper_scraper.twitter import scraper as tscraper

DEFAULT_NUMBER = 2500

def argument_parsing():
    """
    Parse the arguments

    Returns args
    """

    now = datetime.now()

    parser = argparse.ArgumentParser(description="Scrape data from social media")
    parser.add_argument('website', choices=['twitter', 'instagram'],
                        help='The website to crawl for data')
    parser.add_argument('-n', '--number', type=int, default=DEFAULT_NUMBER,
                        dest='number', metavar='Number',
                        help="If data type is images, the number of images to "
                        + "scrape. Else the number of posts to scrape.")
    parser.add_argument('-t', '--tracking', dest='tracking_file', metavar='Tracking File',
                        default='metadata/tracking.txt',
                        help="(Twitter) A file containing a list of phrases, one per line, to track." +
                        " see https://developer.twitter.com/en/docs/tweets/filter-realtime/guides/basic-stream-parameters.html")
    parser.add_argument('-d','--dir',dest='data_directory',metavar="Data Directory",
                        default='./data' + now.strftime('%Y%m%d%H%M%S'),
                        help="The folder to download data to. Default ./dataYYYYMMDDHHMMSS/")
    return parser.parse_args()

def main():
    args = argument_parsing()

    if args.website == 'twitter':
        start_time = time.time()
        tscraper.stream_scrape(tracking_file=args.tracking_file,directory=args.data_directory,number=args.number)
        #tscraper.snowball_scrape('@johnalberse', number=1000, limit_per_user=-1, limit_neighbors_per_node=20)
        elapsed_time = time.time() - start_time
        print("Time elapsed: " + str(elapsed_time))

if __name__ == "__main__":
    main()
