import tweepy
import json
import os.path

## set up OAuth from the keys file. 
## .my_keys (in .gitignore) file takes precedence over the keys file for easily maintaining private keys
try:
    if (os.path.isfile(".my_keys")):
        keys_file = open(".my_keys",'r')
    else: 
        keys_file = open("keys.json",'r')
except OSError as e:
    print("Error opening keys.json")

keys = json.load(keys_file)

consumer_key = keys['websites']['Twitter']['consumer_key']
consumer_secret = keys['websites']['Twitter']['consumer_secret']
access_token = keys['websites']['Twitter']['access_token']
access_token_secret = keys['websites']['Twitter']['access_secret']

auth = tweepy.OAuthHandler(consumer_key,consumer_secret)
auth.set_access_token(access_token,access_token_secret)

api = tweepy.API(auth)