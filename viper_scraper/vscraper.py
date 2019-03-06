import argparse
import string
import sys
import time
from datetime import datetime

from viper_scraper.twitter import scraper as tscraper
from viper_scraper.instagram import scraper as iscraper

DEFAULT_NUMBER = 2500

def main():

    now = datetime.now()

    parser = argparse.ArgumentParser()
    
    subparsers = parser.add_subparsers(title='subcommands',
                                       description='Each social network has its own sub-command and arguments')

    # Twitter parsg
    parser_twit = subparsers.add_parser('twitter', help = 'This scraper is based on the twitter streaming API.'
                                                          ' twitter --help for more information.')
    parser_twit.add_argument('-n', '--number', type=int, default=DEFAULT_NUMBER,
                        dest='number', metavar='Number',
                        help="If data type is images, the number of images to "
                        + "scrape. Else the number of posts to scrape.")
    parser_twit.add_argument('-t', '--tracking', dest='tracking_file', metavar='Tracking File',
                        default='metadata/tracking.txt',
                        help="Path to a text file containing a list of phrases, one per line, to track." +
                        " see https://developer.twitter.com/en/docs/tweets/filter-realtime/guides/basic-stream-parameters.html")
    parser_twit.add_argument('-d','--dir',dest='data_directory',metavar="Data Directory",
                        default='./data' + now.strftime('%Y%m%d%H%M%S'),
                        help="The folder to download data to. Default ./dataYYYYMMDDHHMMSS/")
    parser_twit.set_defaults(func=twitter)

    # Instagram parsing
    parser_insta = subparsers.add_parser('instagram', 
                                         help = 'This is a non-API instagram scraper using Selenium.'
                                         ' instagram --help for more information.')
    parser_insta.add_argument('-d', '--dir_prefix', type=str,
                        default='./data/', help='directory to save results')
    parser_insta.add_argument('-q', '--query', type=str, default='instagram',
                        help="target to crawl, add '#' for hashtags")
    parser_insta.add_argument('-t', '--crawl_type', type=str,
                        default='photos', help="Options: 'photos' | 'followers' | 'following'")
    parser_insta.add_argument('-n', '--number', type=int, default=0,
                        help='Number of posts to download: integer')
    parser_insta.add_argument('-c', '--caption', action='store_true',
                        help='Add this flag to download caption when downloading photos')
    parser_insta.add_argument('-l', '--headless', action='store_true',
                        help='If set, will use PhantomJS driver to run script as headless')
    parser_insta.add_argument('-a', '--authentication', type=str, default=None,
                        help='path to authentication json file')
    parser_insta.add_argument('-f', '--firefox_path', type=str, default=None,
                        help='path to Firefox installation')
    parser_insta.set_defaults(func=instagram)

    args = parser.parse_args()
    args.func(args)

def instagram(args):
    print("parsing insta")
    crawler = iscraper.InstagramCrawler(headless=args.headless, firefox_path=args.firefox_path)
    crawler.crawl(dir_prefix=args.dir_prefix,
                  query=args.query,
                  crawl_type=args.crawl_type,
                  number=args.number,
                  caption=args.caption,
                  authentication=args.authentication)

def twitter(args):
    print("parsing twitter")
    tscraper.stream_scrape(tracking_file=args.tracking_file,directory=args.data_directory,number=args.number)

if __name__ == "__main__":
    main()
