import argparse
import string
import sys
import time
from datetime import datetime

from viper_scraper.twitter import scraper as tscraper
from viper_scraper.instagram import scraper as iscraper
from viper_scraper.twitter import yolo_scrape as yolo_scraper

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
                        help="If photos as limit is true, the number of images to "
                        + "scrape. Else the number of posts to scrape.")
    parser_twit.add_argument('-t', '--tracking', dest='tracking_file', metavar='Tracking File',
                        default='metadata/tracking.txt',
                        help="Path to a text file containing a list of phrases, one per line, to track." +
                        " see https://developer.twitter.com/en/docs/tweets/filter-realtime/guides/basic-stream-parameters.html")
    parser_twit.add_argument('-d','--dir_prefix',dest='data_directory',metavar="Data Directory",
                        default='./data/',
                        help="directory to save results")
    parser_twit.add_argument('--photo_limit', dest='photos_act_as_limiter', action='store_true',
                        help="number refers to number of photos, not tweets. This is the default.")
    parser_twit.add_argument('--status_limit', dest='photos_act_as_limiter', action='store_false',
                        help="number refers to number of tweets, not photos")
    parser_twit.set_defaults(photos_act_as_limiter=True)
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
                        help='Number of posts to download')
    parser_insta.add_argument('-c', '--caption', action='store_true',
                        help='Add this flag to download caption when downloading photos')
    parser_insta.add_argument('-l', '--headless', action='store_true',
                        help='If set, will use PhantomJS driver to run script as headless')
    parser_insta.add_argument('-a', '--authentication', type=str, default=None,
                        help='path to authentication json file')
    parser_insta.add_argument('-f', '--firefox_path', type=str, default=None,
                        help='path to Firefox installation')
    parser_insta.set_defaults(func=instagram)

    # YOLO parsing
    parser_yolo = subparsers.add_parser('yolo',
                        help= 'Use YOLO to scrape images from Twitter')
    parser_yolo.add_argument('-d', '--dir_prefix', type=str,metavar="Data Directory",
                        default='./data/', help='directory to save results')
    parser_yolo.add_argument('-t', '--tracking', dest='tracking_file', metavar='Tracking File',
                        default='metadata/tracking.txt',
                        help="Path to a text file containing a list of phrases, one per line, to track." +
                        " YOLO is applied to tweets from the resultant stream." +
                        " see https://developer.twitter.com/en/docs/tweets/filter-realtime/guides/basic-stream-parameters.html")
    parser_yolo.add_argument('-n', '--number', type=int, default=0,
                        help='Number of images to download')
    # now params for actual YOLO model
    parser_yolo.add_argument('--names', required=True,
                        help="path to names file")
    parser_yolo.add_argument('--config', required=True,
                        help="path to config file")
    parser_yolo.add_argument('--weights', required=True,
                        help="path to weights file")
    parser_yolo.add_argument('-c','--confidence',type=float,default=0.5,
                        help="minimum probability to filter weak detections")
    parser_yolo.add_argument('-th','--threshold', type=float,default=0.3,
                        help="threshold when applying non-maxima suppression")

    parser_yolo.set_defaults(func=yolo)

    args = parser.parse_args()
    args.func(args)

def instagram(args):
    crawler = iscraper.InstagramCrawler(headless=args.headless, firefox_path=args.firefox_path)
    crawler.crawl(dir_prefix=args.dir_prefix,
                  query=args.query,
                  crawl_type=args.crawl_type,
                  number=args.number,
                  caption=args.caption,
                  authentication=args.authentication)

def twitter(args):
    tscraper.stream_scrape(tracking_file=args.tracking_file,directory=args.data_directory,
                           number=args.number,photos_act_as_limiter=args.photos_act_as_limiter)


def yolo(args):
    yolo_scraper.stream_scrape(dir_prefix=args.dir_prefix,
                               tracking_file=args.tracking_file,
                               limit=args.number,
                               names_path=args.names,
                               weights_path=args.weights,
                               config_path=args.config,
                               confidence=args.confidence,
                               threshold=args.threshold)
    

if __name__ == "__main__":
    main()
