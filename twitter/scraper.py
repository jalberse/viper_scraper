import tweepy
import json
import os.path

## set up OAuth from the keys file. 
## .my_keys (in .gitignore) file takes precedence over the keys file for easily maintaining private keys
try:
    if (os.path.isfile("../twitter/.my_keys")):
        keys_file = open("../twitter/.my_keys",'r')
    else: 
        keys_file = open("../twitter/keys.json",'r')
except OSError as e:
    print("Error opening keys file")

keys = json.load(keys_file)

consumer_key = keys['websites']['Twitter']['consumer_key']
consumer_secret = keys['websites']['Twitter']['consumer_secret']
access_token = keys['websites']['Twitter']['access_token']
access_token_secret = keys['websites']['Twitter']['access_secret']

auth = tweepy.OAuthHandler(consumer_key,consumer_secret)
auth.set_access_token(access_token,access_token_secret)

api = tweepy.API(auth)

def scrape(seed_user,images=True,text=False,number=1000,limit_per_node=20):
    print('test')