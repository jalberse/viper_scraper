import tweepy
import json
import urllib.request
import csv
import os.path
import queue
import uuid
from random import randint

DEBUG = 0

"""
This file is mostly a collection of deprecated methods for scraping info from Twitter in various ways
Keeping around in case we want to reuse these ideas later (eg for graph construction), 
but for now the streaming API is better used
"""

def snowball_scrape(seed_user_screen_name, number=1000, limit_per_user=-1, limit_neighbors_per_node=-1):
    """
    DEPRECATED - need to update this method if want to use

    Scrape twitter for images.
    Uses snowball sampling to extract limit_per_node images
    from each user, visiting limit_num_neighbors per user
    until number images have been downloaded.

    If a parameter is -1, there is not limit.

    seed_user -- the user from which the crawl originates
    limt_per_node -- the number of images to scrape per user
    limit_num_neighbors -- The maximum number of neighbors visited per user
    """
    api = get_api()

    # Set up where to save data
    data_dir = ("data/")
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)

    images_dir = ("data/images/")
    if not os.path.exists(images_dir):
        os.makedirs(images_dir)

    k = number # number of images remaining to scrape

    # Queue and set of IDs (not user objects)
    # TODO: string IDs are preferred as "json can much the integer" - consider switching
    to_visit = queue.Queue()
    visited = set()

    user = api.get_user(seed_user_screen_name)
    to_visit.put(user.id)
    visited.add(user.id)

    while ((k > 0) and (to_visit.empty() is not True)):
        user_id = to_visit.get()
        # Scrape this user and update number of images left
        if DEBUG:
            print("Visiting: " + str(user_id))

        k = k - scrape_user_images(user_id=user_id, limit=limit_per_user,
                                   data_dir=data_dir,
                                   api=api)

        # Mark new nodes to visit iff to_visit queue is sufficiently small
        # This reduces GET followers calls, which are severely rate limited
        if to_visit.qsize() < 10:
            # Gather a list of follower/neighbor IDs
            if DEBUG:
                print("Queue low, getting neighbors of " + str(user_id))
            follower_ids = []
            try:
                # TODO: Can we avoid GET followers while queue is of sufficient length?
                # May speed up scraping considerably.
                for follower_id in tweepy.Cursor(api.followers_ids, id=user_id).items():
                    # Check if reached max neighbors to search, if applicable
                    if len(follower_ids) == limit_neighbors_per_node:
                        break
                    follower_ids.append(follower_id)
            except tweepy.error.TweepError:
                if DEBUG:
                    print("Private/suspended/deleted user " + str(user_id) + ", skipping")

            # BFS
            for u_id in follower_ids:
                if u_id not in visited:
                    to_visit.put(u_id)
                    visited.add(u_id)

    if DEBUG:
        print("Done visiting")

def scrape_user_images(user_id,limit,data_dir,api):
    """
    Scrape a single user for images.
    Places all images in data_dir/user_id/ along with
    JSON of user object.
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
    media_files = get_media_urls_from_list(tweets,limit)

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

def get_media_urls_from_list(tweets,limit):
    """
    Returns the set of media URLs from a list of tweets
    """
    cnt = 0
    media_files = set()
    for status in tweets:
        media = status.entities.get('media',[])
        if (len(media) > 0): # each status may have multiple
            for i in range (0, len(media)):
                if (media[i]['type'] == 'photo'):
                    media_files.add(media[i]['media_url'])
                    cnt = cnt + 1
                    print (len(media_files))
                    if (limit != -1 and cnt >= limit): return media_files
    return media_files
