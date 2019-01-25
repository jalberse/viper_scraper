import tweepy
import os.path

# set up OAuth
# .my_keys file takes precedence over the keys file for easily maintaining private keys
try:
    if (os.path.isfile(".my_keys")):
        keys_file = open(".my_keys",'r')
    else: 
        keys_file = open("keys",'r')
except OSError as e:
    print("Error opening keys file")