import argparse
import string
import sys
import time

from twitter import scraper as tscraper

DEFAULT_NUMBER = 2500
DEFAULT_PER_NODE_LIMIT = 100
DEFAULT_FOLLOWER_LIMIT = 10

"""
parser.add_argument('-nl','--node_limit',metavar="Per-Node-Limit",
    type=int,dest='limit_per_node',default=DEFAULT_PER_NODE_LIMIT,
    help="The number of posts/images to extract per node before moving to neighbor. Note: Decreasing "
            " this number increases the time it takes to run, due to twitter rate limits.")
parser.add_argument('-fl','--follower_limit',metavar="Followers-Per-Node",
    type=int,dest='limit_followers_per_node',default=DEFAULT_FOLLOWER_LIMIT,
    help="For snowball sampling, the number of neigbors to visit per node. Visit all neighbors if not listed.")
args = parser.parse_args()
"""

def argument_parsing():
    """
    Parse the arguments

    Returns args
    """

    parser = argparse.ArgumentParser(description="Scrape data from social media")
    parser.add_argument('website', choices=['twitter', 'instagram'],
                        help='The website to crawl for data')
    parser.add_argument('-n', '--number', type=int, default=DEFAULT_NUMBER,
                        dest='number', metavar='Number',
                        help="If data type is images, the number of images to "
                        + "scrape. Else the number of posts to scrape.")
    return parser.parse_args()

def main():
    args = argument_parsing()

    if args.website == 'twitter':
        start_time = time.time()
        tscraper.snowball_scrape(seed_user_screen_name=args.seed_user,
                                 number=args.number,
                                 limit_per_user=args.limit_per_node,
                                 limit_neighbors_per_node=args.limit_followers_per_node)
        elapsed_time = time.time() - start_time
        print("Time elapsed: " + str(elapsed_time))

if __name__ == "__main__":
    main()
