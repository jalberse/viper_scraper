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

q = queue.Queue(maxsize=MAX_QUEUE_SIZE) # tweet Queue - stream produces and threads consumer
csv_lock = threading.Lock()    # Lock for data.csv

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

    def getValue(self):
        with self._lock:
            return self.value

cnt = AtomicCounter()

class YoloStreamListener(tweepy.StreamListener):
    """
    Listen for data
    """
    def __init__(self, directory,names_path,weights_path,config_path,confidence,threshold,api=None,limit=1000):
        super().__init__(api)

        self.limit = limit
        self.stop_flag = False

        self.LABELS = open(names_path).read().strip().split("\n")
        self.COLORS = np.random.randint(0,255,size=(len(self.LABELS),3),dtype="uint8")

        # Threads to process tweets from queue
        num_worker_threads = 16
        self.threads = []
        for i in range(num_worker_threads):
            t = TweetConsumerThread(directory,weights_path,config_path,confidence,threshold,self.COLORS,self.LABELS,limit)
            t.daemon = True
            t.start()
            self.threads.append(t)

        # TODO: A thread for writing to data.csv from consumers' outputs - need to be careful on closing

    def request_stop(self):
        self.stop_flag = True

    # Producer - from twitter stream
    def on_status(self, status):
        if cnt.getValue() > self.limit or self.stop_flag:
            if cnt.getValue() > self.limit:
                print("Tweet limit reached, exiting stream (consuming queue)...")
            if self.stop_flag:
                print("Exiting stream (consuming queue)...")
            # Notify consumer threads to stop processing tweets
            # Necessary - consumer threads call C code for YOLO, and may segfault if not properly closed
            # TODO: Sometimes this blocks - figure out why
            for t in self.threads:
                q.put(None) # tell consumers we are done
            # Disconnect stream once they all stop
            for t in self.threads:
                t.join()
            if cnt.getValue() > self.limit:
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
    def __init__(self,directory,weights_path,config_path,confidence,threshold,colors,labels,limit,
                    group=None,target=None,name=None,args=(),kwargs=None,verbose=None):
        super().__init__()
        self.directory = directory
        self.config_path = config_path
        self.confidence = confidence
        self.threshold = threshold
        self.target = target
        self.name = name
        self.limit = limit

        self.COLORS = colors
        self.LABELS = labels

        # Load YOLO
        self.net = cv2.dnn.readNetFromDarknet(config_path,weights_path)

    def run(self):
        while True:
            tweet = q.get()
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
        media_urls, _ = twitter_scraper.get_media_urls(status)
        if len(media_urls) == 0:
            return False # No images to download
        csv_to_image_file_path = ''
        for url in media_urls:
            file_id = uuid.uuid4().hex
            filename = os.path.join(self.directory,'data/images/', file_id + ".jpg")
            try:
                urllib.request.urlretrieve(url, filename)
            except Exception as e:
                print(e)    # likely HTTP error - user deleted images etc
                return False # skip this tweet but continue streaming
            csv_to_image_file_path = os.path.join("data/images/",file_id + ".jpg")

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

                    if (confidence > self.confidence):
                        box = detection[0:4] * np.array([W,H,W,H])
                        (center_x,center_y,width,height) = box.astype("int")
                        x = int(center_x - (width / 2))
                        y = int(center_y - (height / 2))

                        bounding_boxes.append([x,y,int(width),int(height)])
                        confidences.append(float(confidence))
                        labels.append(label)
            
            # non-maxima suppression
            idxs = cv2.dnn.NMSBoxes(bounding_boxes, confidences, self.confidence, self.threshold)

            # draw the bounding boxes for the marked up version of the image
            if len(idxs) > 0:
                for i in idxs.flatten():
                    (x,y) = (bounding_boxes[i][0], bounding_boxes[i][1])
                    (w,h) = (bounding_boxes[i][2], bounding_boxes[i][3])
                    color = [int(c) for c in self.COLORS[labels[i]]]
                    cv2.rectangle(img=image, pt1=(x,y), pt2=(x + w, y + h),color=color, thickness=2)
                    text = "{}: {:.4f}".format(self.LABELS[labels[i]], confidences[i])
                    cv2.putText(image,text,(x, y - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

            # create a dict of labels:[confidences]
            # populate dict with ALL labels associated with empty arrays
            detected = {}
            for l in self.LABELS:
                detected[l] = []

            if len(idxs) > 0:
                for i in idxs.flatten():
                    detected[self.LABELS[labels[i]]].append(confidences[i])
                
            # save json file to disk
            filename_json = os.path.join(self.directory,'data/images/',file_id + ".json")
            with open(filename_json,'w') as f:
                json.dump(detected,f)

            csv_to_json_file_path = os.path.join('data/images/',file_id + ".json")
            
            # Save the image with bounding boxes to disk
            filename_marked = os.path.join(self.directory,'data/images/', file_id + "_marked.jpg")
            cv2.imwrite(filename_marked, image)

            csv_to_marked_image_file_path = os.path.join("data/images/",file_id + "marked.jpg")

            # Format data for writing to CSV
            # Handle nullable objects in tweet
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
            # Handle getting full text of tweet (deals with truncation)
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
                    writer.writerow([status.user.id_str, status.id_str,text,csv_to_image_file_path,
                                csv_to_marked_image_file_path,status.created_at,
                                status.source,status.truncated,status.in_reply_to_status_id_str,status.in_reply_to_user_id_str,
                                status.in_reply_to_screen_name,lon,lat,place_full_name,
                                place_type,place_id,place_url,status.quote_count,status.reply_count,
                                status.retweet_count,status.favorite_count,status.lang,csv_to_json_file_path])
                csv_lock.release()
                return True # Succesfully processed tweet
            except OSError:
                print(str(OSError) + "Error writing to CSV")
                print("On tweet " +str(self.cnt))
                return False 

def stream_scrape(dir_prefix,tracking_file,limit,weights_path,config_path,names_path,confidence,threshold):
    api = twitter_scraper.get_api()

    if not os.path.exists(dir_prefix):
        os.makedirs(dir_prefix)

    twitter_dir = os.path.join(dir_prefix,"twitter_yolo/")

    data_dir = os.path.join(twitter_dir,'data/')
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)

    images_dir = os.path.join(twitter_dir,'data/images/')
    if not os.path.exists(images_dir):
        os.makedirs(images_dir)

    # Create tracking param
    try:
        with open(tracking_file, 'r') as f:
            tracking = f.read().splitlines()
    except OSError:
        print("Error opening tracking.txt")
        return

    # CSV file - create and write header if necessary
    try:
        filename = os.path.join(twitter_dir,'data.csv')
        with open(filename, 'a+') as f:
            writer = csv.writer(f)
            if os.path.getsize(filename) == 0:
                writer.writerow(['user_id', 'tweet_id', 'text','image_file','marked_up_image_file',
                    'created_at','source','truncated','in_reply_to_status_id',
                    'in_reply_to_user_id','in_reply_to_screen_name','longitude','latitude',
                    'place_full_name','place_type','place_id','place_url','quote_count',
                    'reply_count','retweet_count','favorite_count','lang','detected_file'])
    except OSError:
        print("Could not create data.csv")

    print("Starting stream...")

    stream_listener = YoloStreamListener(directory=twitter_dir,limit=limit,names_path=names_path,
                                        weights_path=weights_path,config_path=config_path,
                                        confidence=confidence,threshold=threshold)
    stream = tweepy.Stream(auth=api.auth, listener=stream_listener,
                           tweet_mode='extended', stall_warnings=True)
    stream.filter(track=tracking, is_async = True) # to unblock, is_async = True 

    input("Press ENTER to exit stream at any time\n")

    stream_listener.request_stop()
