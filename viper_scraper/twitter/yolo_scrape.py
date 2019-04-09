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

from . import scraper as twitter_scraper

class YoloStreamListener(tweepy.StreamListener):
    """
    Listen for data
    """
    def __init__(self, directory,names_path,weights_path,config_path,confidence,threshold, api=None, limit=1000):
        super().__init__(api)
        self.directory = directory
        self.names_path=names_path
        self.weights_path=weights_path
        self.config_path=config_path
        self.confidence=confidence
        self.threshold=threshold
        self.limit = limit
        self.cnt = 0

        # for marking up images
        self.LABELS = open(names_path).read().strip().split("\n")
        self.COLORS = np.random.randint(0,255,size=(len(self.LABELS),3),dtype="uint8")

        # Load YOLO
        self.net = cv2.dnn.readNetFromDarknet(config_path,weights_path)

    def on_status(self, status):
        if status.text.startswith('RT'):
            return True # Ignore RTs to avoid repeat data
        media_urls, _ = twitter_scraper.get_media_urls(status)
        csv_to_image_file_path = ''
        for url in media_urls:
            file_id = uuid.uuid4().hex
            filename = os.path.join(self.directory,'data/images/', file_id + ".jpg")
            try:
                urllib.request.urlretrieve(url, filename)
            except urllib.error.HTTPError:
                print("HTTPError, skipping media")
                return True # skip this tweet but continue streaming
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
                    cv2.rectangle(image, (x,y), (x + w, y + h),color, 2)
                    text = "{}: {:.4f}".format(self.LABELS[labels[i]], confidences[i])
                    cv2.putText(image,text,(x, y - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

            # create a dict of labels:[confidences]
            # populate dict with ALL labels associated with empty arrays
            detected = {}
            for l in self.LABELS:
                detected[l] = []

            if len(idxs) > 0:
                for i in idxs.flatten():
                    # TODO append the confidence to the label's associated array
                    detected[self.LABELS[labels[i]]].append(confidences[i])
                
            # save this data to disk
            filename_json = os.path.join(self.directory,'data/images/',file_id + ".json")
            with open(filename_json,'w') as f:
                json.dump(detected,f)

            csv_to_json_file_path = os.path.join('data/images/',file_id + ".json")
            
            # Save the image with bounding boxes to disk
            filename_marked = os.path.join(self.directory,'data/images/', file_id + "_marked.jpg")
            cv2.imwrite(filename_marked, image)

            csv_to_marked_image_file_path = os.path.join("data/images/",file_id + "marked.jpg")

            # TODO place file location of confidences JSON file into csv
            # Write stuff to CSV
            try:
                with open(os.path.join(self.directory,'data.csv'), 'a+') as f:
                    writer = csv.writer(f)
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

                    # TODO: Write confidences etc to csv

                    # Finally write data to csv line
                    writer.writerow([status.user.id_str, status.id_str,text,csv_to_image_file_path,
                                csv_to_marked_image_file_path,status.created_at,
                                status.source,status.truncated,status.in_reply_to_status_id_str,status.in_reply_to_user_id_str,
                                status.in_reply_to_screen_name,lon,lat,place_full_name,
                                place_type,place_id,place_url,status.quote_count,status.reply_count,
                                status.retweet_count,status.favorite_count,status.lang,csv_to_json_file_path])
            except OSError:
                print(str(OSError) + "Error writing to CSV")
                print("On tweet " +str(self.cnt))
                return False 

    def on_error(self, status_code):
        if status_code == 420:
            #returning False in on_data disconnects the stream
            return False
        return False

def stream_scrape(dir_prefix,tracking_file,limit,weights_path,config_path,names_path,confidence,threshold):
    print("yolo")
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
    stream.filter(track=tracking) # To unblock, asynch = True