import tweepy
import json
import os.path
import queue

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

api = tweepy.API(auth_handler=auth,wait_on_rate_limit=True)


def scrape(seed_user_screen_name,number=1000,limit_per_user=-1,limit_neighbors_per_node=-1):
    """ 
    Scrape twitter for images. 
    Uses breadth-first-search to extract limit_per_node images
    from each user, visiting limit_num_neighbors per user
    until number images have been downloaded

    If a parameter is -1, there is not limit

    seed_user -- the user from which the crawl originates
    limt_per_node -- the number of images to scrape per user
    limit_num_neighbors -- The maximum number of neighbors visited per user
    """

    # Set up where to save data
    data_dir = ("../data/")
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
    
    k = number # number of images remaining to scrape

    # Queue and set of IDs (not user objects)
    # TODO: string IDs are preferred as "json can much the integer" - consider switching
    to_visit = queue.Queue()
    visited = set()

    # Get seed user and enqueue its id
    user = api.get_user(seed_user_screen_name)
    to_visit.put(user.id)
    visited.add(user.id)

    while ((to_visit.empty() is not True) and (k > 0)):
        user_id = to_visit.get()
        # Scrape this user and update number of images left
        k = k - scrape_user(user_id=user_id,limit=limit_per_user,data_dir=data_dir)

        if (DEBUG):
            print("Visiting: " + str(user_id))

        # Gather a list of follower/neighbor IDs
        follower_ids = []
        for follower_id in tweepy.Cursor(api.followers_ids, id=user_id).items():
            # Check if reached max neighbors to search, if applicable
            if (limit_neighbors_per_node != -1 and len(follower_ids) == limit_neighbors_per_node): break
            follower_ids.append(follower_id)
        # BFS
        for u_id in follower_ids:
            if (u_id not in visited):
                to_visit.put(u_id)
                visited.add(u_id)
    
    if (DEBUG):
        print("Done visiting")


def scrape_user(user_id,limit,data_dir):
    """
    Scrape a single user for images.
    Returns the number of images scraped

    user -- the twitter user object to scrape
    limit -- the maximum number of images to scrape from this user. If -1, no limit
    data_dir -- the directory to save images to
    """
    return 100 # TODO just testing