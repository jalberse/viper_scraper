import argparse
import string
import sys

from twitter import scraper as tscraper

parser = argparse.ArgumentParser(description="Scrape data from social media")

parser.add_argument('website',choices=['twitter','instagram'],
    help='The website to crawl for data')
parser.add_argument('seed_user',
    help='The seed user handle, e.g. @Twitter')
parser.add_argument('-n','--number',type=int,default=1000,
    dest='number',metavar='Number',
    help="If data type is images, the number of images to scrape. Else the number of posts to scrape.")
parser.add_argument('-l','--limit',metavar="Per-Node-Limit",
    type=int,dest='limit_per_node',default=20,
    help="The number of posts/images to extract per node before moving to neighbor")
args = parser.parse_args()

if (args.website=='twitter'): 
    tscraper.scrape(seed_user=args.seed_user,number=args.number,limit_per_node=args.limit_per_node)
