import argparse
import string
import sys

from twitter import scraper as tscraper

DEFAULT_NUMBER = 2500
DEFAULT_PER_NODE_LIMIT = 100
DEFAULT_FOLLOWER_LIMIT = 10

parser = argparse.ArgumentParser(description="Scrape data from social media",
                                epilog="For snowball sampling, reducing per-node-limit and followers-per-node will " +
                                "reduce locality of data collected (ie increase depth of the graph traversed " +
                                "at the cost of increased processing time to due Twitter API rate limits.")

parser.add_argument('website',choices=['twitter','instagram'],
    help='The website to crawl for data')
parser.add_argument('seed_user',
    help='The seed user handle, e.g. @Twitter')
parser.add_argument('-n','--number',type=int,default=DEFAULT_NUMBER,
    dest='number',metavar='Number',
    help="If data type is images, the number of images to scrape. Else the number of posts to scrape.")
parser.add_argument('-nl','--node_limit',metavar="Per-Node-Limit",
    type=int,dest='limit_per_node',default=DEFAULT_PER_NODE_LIMIT,
    help="The number of posts/images to extract per node before moving to neighbor. Note: Decreasing "
            " this number increases the time it takes to run, due to twitter rate limits.")
parser.add_argument('-fl','--follower_limit',metavar="Followers-Per-Node",
    type=int,dest='limit_followers_per_node',default=DEFAULT_FOLLOWER_LIMIT,
    help="For snowball sampling, the number of neigbors to visit per node. Visit all neighbors if not listed.")
args = parser.parse_args()

if (args.website=='twitter'): 
    tscraper.snowball_scrape(seed_user_screen_name=args.seed_user,number=args.number,
                    limit_per_user=args.limit_per_node,
                    limit_neighbors_per_node=args.limit_followers_per_node)
