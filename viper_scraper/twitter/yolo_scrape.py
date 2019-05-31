import tweepy
import numpy as np
import time
import cv2
import os
import queue
import uuid
import json
import urllib.request
import csv
import threading
import _thread

from . import scraper as twitter_scraper

MAX_QUEUE_SIZE = 10000

# TODO: Go through code and change all the previous self.LABELS etc to self.yolo.LABELS... ugh
class Yolo:
    def __init__(self,names_path,weights_path,config_path,confidence,threshold):
        self.LABELS = open(names_path).read().strip().split("\n")
        self.COLORS = np.random.randint(0,255,size=(len(self.LABELS),3),dtype="uint8")
        self.confidence = confidence
        self.threshold = threshold
        self.config_path = config_path
        self.weights_path = weights_path


#TODO this belongs in a utility file
class AtomicCounter:
    """
    Thread-safe counter
    """
    def __init__(self,val=0):
        self.value = val
        self._lock = threading.Lock()

    def increment(self,num=1):
        with self._lock:
            self.value += num
            return self.value

    def get_value(self):
        with self._lock:
            return self.value

cnt = AtomicCounter()                   # Count number of tweets or images downloaded
q = queue.Queue(maxsize=MAX_QUEUE_SIZE) # tweet Queue
csv_lock = threading.Lock()             # Lock for data.csv

class YoloStreamListener(tweepy.StreamListener):
    """
    Listen for data
    """
    def __init__(self,directory,yolo=None,api=None,limit=1000):
        super().__init__(api)
        # TODO: Allow user to specify if they want to limit by number of tweets or number of photos (and time?)

        self.limit = limit
        self.stop_flag = False

        self.yolo = yolo

        # Threads to process tweets from queue
        num_worker_threads = 8
        self.threads = []
        for i in range(num_worker_threads):
            t = TweetConsumerThread(directory,limit,self.yolo)
            t.daemon = True
            t.start()
            self.threads.append(t)

        # TODO: A thread for writing to data.csv from consumers' outputs - need to be careful on closing

    def request_stop(self):
        self.stop_flag = True

    # Producer - from twitter stream
    def on_status(self, status):
        if cnt.get_value() > self.limit or self.stop_flag:
            if cnt.get_value() > self.limit:
                print("Tweet limit reached, exiting stream (consuming queue)...")
            if self.stop_flag:
                print("Exiting stream (consuming queue)...")
            # Notify consumer threads to stop processing tweets
            # TODO: Sometimes this still blocks - figure out why
            for t in self.threads:
                q.put(None) # tell consumers we are done
            # Disconnect stream once they all stop
            for t in self.threads:
                t.join()
            if cnt.get_value() > self.limit:
                print("Done. Press ENTER to exit.")
            else:
                print("Done")
            return False   # Stop stream
        if not q.full():
            q.put(status)

    def on_error(self, status_code):
        if status_code == 420:
            #returning False in on_data disconnects the stream
            return False
        return False

class TweetConsumerThread(threading.Thread):
    def __init__(self,directory,limit,yolo=None):
        super().__init__()
        self.directory = directory
        self.limit = limit
        self.yolo = yolo
        if yolo is not None:
            self.net = cv2.dnn.readNetFromDarknet(self.yolo.config_path,self.yolo.weights_path)

    def run(self):
        while True:
            tweet = q.get() # blocks until queue has an item in it
            if tweet is None: # Producer has indicated we are done
                break
            if self.process_tweet(tweet): # if an image was downloaded
                curr_cnt = cnt.increment()
                if curr_cnt % 25 is 0:
                    print(str(curr_cnt) + " tweets downloaded")
                    print(str(q.qsize()) + " tweets in queue")
            q.task_done()

    def process_tweet(self, status):
        """
        If a tweet contains an image: downloads image, marks up with YOLO, saves
        tweet data, images, confidences

        Returns True if downloaded an image
        Returns False if tweet did not contain an image or was a RT
        """
        if status.text.startswith('RT'):
            return False # Ignore RTs to avoid repeat data
        # TODO: Use extended_entities for media URLs instead! 
        #       Have 4 columns for each tweet (image, marked image, JSON)
        #       Since 4 is maximum number of media files.
        #       Will also probably now return -1/0/1/2/3/4 now instead for counting pics... 
        # TODO: This will require a rework of tracking_generation.py - probably just is_above_threshold
        #       Which now will check all photos in a tweet, and obviously how we read those confidences in
        media_urls, _ = get_media_urls(status)
        if len(media_urls) == 0:
            return False # No images to download

        image_paths = ['' for i in range (4)]
        marked_image_paths = ['' for i in range (4)]
        confidence_json_paths = ['' for i in range (4)]

        csv_to_image_file_path = ''
        for i, url in enumerate(media_urls):
            # Download image with unique filename - this ID is used for json and marked image as well
            file_id = uuid.uuid4().hex
            filename = os.path.join(self.directory,'data/images/', file_id + ".jpg")
            try:
                urllib.request.urlretrieve(url, filename)
            except Exception as e:
                print(e)     # likely HTTP error - user deleted image etc
                return False # skip this tweet

            image_paths[i] = os.path.join("data/images/",file_id + ".jpg")

            # If using YOLO, run image through YOLO and save image with bounding boxes and JSON file with confidences
            if self.yolo is not None:
                confidence_json_paths[i], marked_image_paths[i] = self.run_yolo(filename,file_id)
            
        # Format data for writing to CSV
        lon = ''
        lat = ''
        if status.coordinates is not None:
            lon = status.coordinates["coordinates"][0]
            lat = status.coordinates["coordinates"][1]
        place_full_name = ''
        place_type = ''
        place_id = ''
        place_url = ''
        if status.place is not None:
            place_full_name = status.place.full_name
            place_type = status.place.place_type
            place_id = status.place.id
            place_url = status.place.url

        # Get full text of tweet (deals with truncation)
        text = ''
        try:
            if hasattr(status, 'extended_tweet'):
               text = status.extended_tweet['full_text']
            else:
                text = status.text
        except AttributeError:
            print('attribute error: ' + status.text)

        # Write to CSV
        try:
            csv_lock.acquire()
            with open(os.path.join(self.directory,'data.csv'), 'a+') as f:
                writer = csv.writer(f)
                writer.writerow([status.user.id_str,status.id_str,text] + image_paths + marked_image_paths + confidence_json_paths +
                            [status.source,status.truncated,status.in_reply_to_status_id_str,status.in_reply_to_user_id_str,
                            status.in_reply_to_screen_name,lon,lat,place_full_name,
                            place_type,place_id,place_url,status.quote_count,status.reply_count,
                            status.retweet_count,status.favorite_count,status.lang])
            csv_lock.release()
            return True # Succesfully processed tweet
        except OSError:
            print(str(OSError) + "Error writing to CSV")
            print("On tweet " +str(self.cnt))
            return False 

    def run_yolo(self, filename, file_id):
        '''
        Runs image specified by filename through YOLO
        Saves image with bounding box, JSON with confidences
        returns tuple (csv_to_json_filepath,csv_to_marked_image_filepath)
        '''
        # We have local file - now run it through YOLO
        # this code derived from
        # https://www.pyimagesearch.com/2018/11/12/yolo-object-detection-with-opencv/

        image = cv2.imread(filename)
        (H, W) = image.shape[:2]

        ln = self.net.getLayerNames()
        ln = [ln[i[0] -1] for i in self.net.getUnconnectedOutLayers()]

        blob = cv2.dnn.blobFromImage(image, 1/ 255.0, (416, 416), swapRB=True, crop=False)
        self.net.setInput(blob)
        layerOutputs=self.net.forward(ln)

        bounding_boxes = []
        confidences = []
        labels = []

        for output in layerOutputs:
            for detection in output:
                scores = detection[5:]
                label = np.argmax(scores)
                confidence = scores[label]

                if (confidence > self.yolo.confidence):
                    box = detection[0:4] * np.array([W,H,W,H])
                    (center_x,center_y,width,height) = box.astype("int")
                    x = int(center_x - (width / 2))
                    y = int(center_y - (height / 2))
                    bounding_boxes.append([x,y,int(width),int(height)])
                    confidences.append(float(confidence))
                    labels.append(label)
            
        # non-maxima suppression
        idxs = cv2.dnn.NMSBoxes(bounding_boxes, confidences, self.yolo.confidence, self.yolo.threshold)

        # draw the bounding boxes for the marked up version of the image
        if len(idxs) > 0:
            for i in idxs.flatten():
                (x,y) = (bounding_boxes[i][0], bounding_boxes[i][1])
                (w,h) = (bounding_boxes[i][2], bounding_boxes[i][3])
                color = [int(c) for c in self.yolo.COLORS[labels[i]]]
                cv2.rectangle(img=image, pt1=(x,y), pt2=(x + w, y + h),color=color, thickness=2)
                text = "{}: {:.4f}".format(self.yolo.LABELS[labels[i]], confidences[i])
                cv2.putText(image,text,(x, y - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

        # create a dict of labels:[confidences]
        # populate dict with ALL labels associated with empty arrays
        detected = {}
        for l in self.yolo.LABELS:
            detected[l] = []

        if len(idxs) > 0:
            for i in idxs.flatten():
                detected[self.yolo.LABELS[labels[i]]].append(confidences[i])
                
        # save json file to disk
        filename_json = os.path.join(self.directory,'data/confidences/',file_id + ".json")
        with open(filename_json,'w') as f:
            json.dump(detected,f)

        csv_to_json_file_path = os.path.join('data/images/',file_id + ".json")
            
        # Save the image with bounding boxes to disk
        filename_marked = os.path.join(self.directory,'data/images/', file_id + "_marked.jpg")
        cv2.imwrite(filename_marked, image)

        csv_to_marked_image_file_path = os.path.join("data/images/",file_id + "marked.jpg")

        return csv_to_json_file_path, csv_to_marked_image_file_path

def stream_scrape(dir_prefix,tracking,limit,yolo):
    api = get_api()

    if not os.path.exists(dir_prefix):
        os.makedirs(dir_prefix)

    twitter_dir = os.path.join(dir_prefix,"twitter_yolo/")

    data_dir = os.path.join(twitter_dir,'data/')
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)

    images_dir = os.path.join(twitter_dir,'data/images/')
    if not os.path.exists(images_dir):
        os.makedirs(images_dir)

    confidences_dir = os.path.join(twitter_dir,'data/confidences/')
    if not os.path.exists(confidences_dir):
        os.makedirs(confidences_dir)

    # CSV file - create and write header if necessary
    try:
        filename = os.path.join(twitter_dir,'data.csv')
        with open(filename, 'a+') as f:
            writer = csv.writer(f)
            if os.path.getsize(filename) == 0:
                writer.writerow(['user_id', 'tweet_id', 'text',
                    'image_file_0','image_file_1','image_file_2','image_file_3',
                    'marked_up_image_file_0','marked_up_image_file_1','marked_up_image_file_2','marked_up_image_file_3',
                    'csv_to_json_file_path_0','csv_to_json_file_path_1','csv_to_json_file_path_2','csv_to_json_file_path_3',
                    'created_at','source','truncated','in_reply_to_status_id',
                    'in_reply_to_user_id','in_reply_to_screen_name','longitude','latitude',
                    'place_full_name','place_type','place_id','place_url','quote_count',
                    'reply_count','retweet_count','favorite_count','lang'])
    except OSError:
        print("Could not create data.csv")

    stream_listener = YoloStreamListener(directory=twitter_dir,limit=limit,yolo=yolo)

    print("Starting stream...")

    while cnt.get_value() < limit:
        try:
            stream = tweepy.Stream(auth=api.auth, listener=stream_listener,
                                   tweet_mode='extended', stall_warnings=True)
            stream.filter(track=tracking, is_async = True) # to unblock, is_async = True
            print("Stream connected")
            input("Press ENTER to exit stream at any time\n")
                # Blocking - if ENTER is pressed, will break from loop and request stream_listener
                # to stop. If ENTER is not pressed and an error occurs, the stream will reconnect
            break
        except Exception as e:
            print(e)
            print("Error occured, reconnecting stream...")
            continue

    stream_listener.request_stop()


#####################
# Utility functions #
#####################

def get_api():
    """
    Handles OAuth and returns the tweepy API
    """
    try:
        ## TODO: Fix paths for best practice compliance
        if os.path.isfile(".my_keys"):
            keys_file = open(".my_keys", 'r')
        else:
            keys_file = open("config/keys.json", 'r')
    except OSError:
        print("Error opening keys file")

    keys = json.load(keys_file)

    consumer_key = keys['websites']['Twitter']['consumer_key']
    consumer_secret = keys['websites']['Twitter']['consumer_secret']
    access_token = keys['websites']['Twitter']['access_token']
    access_token_secret = keys['websites']['Twitter']['access_secret']

    auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_token, access_token_secret)

    return tweepy.API(auth_handler=auth, wait_on_rate_limit=True,
                      wait_on_rate_limit_notify=True)

def get_media_urls(tweet):
    """
    Returns the set of media urls for a given tweet
    """
    try:
        media = tweet.extended_entities.get('media', [])
    except AttributeError as e:
        return [], 0
    media_urls = []
    cnt = 0
    if len(media) > 0:
        for i in range(0, len(media)):
            if media[i]['type'] == 'photo':
                media_urls.append(media[i]['media_url'])
                cnt = cnt + 1
    return media_urls, cnt