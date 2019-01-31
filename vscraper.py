import argparse
import string
import twitterscraper

parser = argparse.ArgumentParser(description="Scrape data from social media")

parser.add_argument('website',choices=['twitter','instagram'],
    nargs=1,
    help='The website to crawl for data')
parser.add_argument('seed user',nargs=1,
    help='The seed user handle, e.g. @Twitter')
parser.add_argument('-t','--type',choices=['images','text','all'],
    nargs=1,default='images',dest='data_type',
    help="The data type to collect. Images only by default. 'all' is images + text")
parser.add_argument('-n','--number',type=int,nargs=1,default=1000,
    dest='num',metavar='Number',
    help="If data type is images, the number of images to scrape. Else the number of posts to scrape.")
args = parser.parse_args()