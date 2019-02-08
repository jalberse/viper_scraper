import tweepy
import json
import urllib.request
import os.path
import queue
import uuid
from random import randint

DEBUG = 1

## set up OAuth from the keys file. 
## .my_keys (in .gitignore) file takes precedence over the keys file for easily maintaining private keys
try:
    ## TODO: Fix paths for best practice compliance
    if (os.path.isfile(".my_keys")):
        keys_file = open(".my_keys",'r')
    else: 
        keys_file = open("metadata/keys.json",'r')
except OSError as e:
    print("Error opening keys file")

keys = json.load(keys_file)

consumer_key = keys['websites']['Twitter']['consumer_key']
consumer_secret = keys['websites']['Twitter']['consumer_secret']
access_token = keys['websites']['Twitter']['access_token']
access_token_secret = keys['websites']['Twitter']['access_secret']

auth = tweepy.OAuthHandler(consumer_key,consumer_secret)
auth.set_access_token(access_token,access_token_secret)

api = tweepy.API(auth_handler=auth,wait_on_rate_limit=True,
                wait_on_rate_limit_notify=True)


def snowball_scrape(seed_user_screen_name,number=1000,limit_per_user=-1,limit_neighbors_per_node=-1):
    """ 
    Scrape twitter for images. 
    Uses snowball sampling to extract limit_per_node images
    from each user, visiting limit_num_neighbors per user
    until number images have been downloaded

    If a parameter is -1, there is not limit

    seed_user -- the user from which the crawl originates
    limt_per_node -- the number of images to scrape per user
    limit_num_neighbors -- The maximum number of neighbors visited per user
    """

    # Set up where to save data
    data_dir = ("data/")
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
    
    k = number # number of images remaining to scrape

    # Queue and set of IDs (not user objects)
    # TODO: string IDs are preferred as "json can much the integer" - consider switching
    to_visit = queue.Queue()
    visited = set()

    user = api.get_user(seed_user_screen_name)    
    to_visit.put(user.id)
    visited.add(user.id)

    while ((to_visit.empty() is not True) and (k > 0)):
        user_id = to_visit.get()
        # Scrape this user and update number of images left
        if (DEBUG): print("Visiting: " + str(user_id))

        k = k - scrape_user_images(user_id=user_id,limit=limit_per_user,data_dir=data_dir)

        # Gather a list of follower/neighbor IDs
        if (DEBUG): print("Getting neighbors of " + str(user_id))
        follower_ids = []
        try:
            # TODO: Can we avoid GET followers while queue is of sufficient length?
            # May speed up scraping considerably.
            for follower_id in tweepy.Cursor(api.followers_ids, id=user_id).items():
                # Check if reached max neighbors to search, if applicable
                if (limit_neighbors_per_node != -1 and len(follower_ids) == limit_neighbors_per_node): break
                follower_ids.append(follower_id)
        except tweepy.error.TweepError:
            if (DEBUG): print("Private/suspended/deleted user " + str(user_id) + ", skipping")

        # BFS
        for u_id in follower_ids:
            if (u_id not in visited):
                to_visit.put(u_id)
                visited.add(u_id)
    
    if (DEBUG):
        print("Done visiting")

# TODO: It may be desirable to associate saved images with JSON of status for later searching
def scrape_user_images(user_id,limit,data_dir):
    """
    Scrape a single user for images. Gets all images.
    Returns the number of images scraped.

    user -- the twitter user object to scrape
    limit -- the maximum number of images to scrape from this user. If -1, no limit
    data_dir -- the directory to save images to
    """
    if (DEBUG): print("Scraping user " + str(user_id))
    
    user = api.get_user(user_id)
    if (user.protected == True): return 0

    # Create directory to store user's data and images
    user_dir = os.path.join(data_dir,str(user_id))
    if not os.path.exists(user_dir):
            os.makedirs(user_dir)
    else:
        return 0 #already have user data

    # Save user data
    f = open(os.path.join(user_dir,str(user_id) + ".json"),'w')
    f.write(str(vars(user)))
    f.close()
    
    # Get all tweets from user
    # TODO: Could improve speed by grabbing images inside this loop until hit max
    tweets = api.user_timeline(id=user_id,count=200)
    if len(tweets) is not 0:
        last_id = tweets[-1].id
    else: return 0 # no tweets to scrape
    while (True):
        tweets_to_append = api.user_timeline(id=user_id,count=200,
                                        max_id=last_id-1)
        if (len(tweets_to_append)==0):
            break
        else:
            last_id = tweets_to_append[-1].id-1
            tweets = tweets + tweets_to_append
    
    # Collect a set of image URLs from the user
    media_files = get_media_urls(tweets,limit)
        
    # Download the images
    n = 0 # num of images downloaded from user
    for media_file in media_files:
        try:
            urllib.request.urlretrieve(media_file,
                os.path.join(user_dir, str(user_id) + "_" + str(n) + ".jpg"))
            n = n + 1
        except urllib.error.HTTPError:
            if(DEBUG): print("HTTPError, skipping media")
    return n

def get_media_urls(tweets,limit):
    cnt = 0
    media_files = set()
    for status in tweets:
        media = status.entities.get('media',[])
        if (len(media) > 0): # each status may have multiple
            for i in range (0, len(media)):
                if (media[i]['type'] == 'photo'):
                    media_files.add(media[i]['media_url'])
                    cnt = cnt + 1
                    if (limit != -1 and cnt >= limit): return media_files
    return media_files