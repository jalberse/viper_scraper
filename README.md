# Viper Scraper

## Set-Up

Before using any script, run `pipenv shell` to enter the virtual environment.

Using the Twitter scraper requires registering as a Twitter developer and providing authentication keys. Place your keys in either *.my_keys* (in .gitignore) or *config/keys.json*. See the [Twitter Developer page](https://developer.twitter.com/).

## Scraping Twitter

```
viper_scraper.py twitter [-h] [-d Data Directory] [-t Tracking File] 
                         [-l Limit] [--photos_as_limit]
```

`-d Data Directory` : Directory to save results to

`-t Tracking File` : Path to a text file containing a list of phrases, one
                    per line, to track. See the Twitter page for [filteringrealtime tweets](https://developer.twitter.com/en/docstweets/filter-realtime/guidesbasic-stream-parameters.html).


`-l Limit` : If photos as limit is true, the approximate number of
                        images to scrape. Else the approximate number of tweets
                        to scrape.

`--photos_as_limit` : If present, Limit refers to the number of images to scrape                        rather than number of tweets

The Twitter scraper filters realtime tweets using the [Twitter API](https://developer.twitter.com/en/docs.html). Text, metadata, and references to downloaded images are stored in data.csv under the specified directory.

#### YOLO integration with Twitter

```
python viper_scraper.py yolo ...
```

The VIPER scraper also integrates You Only Look Once ([YOLO](https://pjreddie.com/darknet/yolo/)) real-time object detection.

For each tweet that passes the filter, the scraper will:

1. Download the original image, if present.
2. Save a version of the image with bounding boxes and predictions labelled
3. Save a .json file containing the confidences for each class
4. Save text and metadata, along with references to these files, in data.csv under the specified directory

```
viper_scraper.py yolo [-h] [-d Data Directory] [-t Tracking File]
                      [-l Limit] [--photos_as_limit] --names NAMES
                      --config CONFIG --weights WEIGHTS [-c CONFIDENCE]
                      [-th THRESHOLD]
```

In addition to the arguments shared by the basic Twitter scraper, YOLO integration takes these additional arguments:

`--names NAMES` : A file containing the names, one per line, associated with the weights and config file for YOLO, e.g. [coco.names](https://github.com/pjreddie/darknet/blob/master/data/coco.names).

`--config CONFIG` : Config file for YOLO, e.g. [yolov3.cfg](https://github.com/pjreddie/darknet/blob/master/cfg/yolov3.cfg).

`--weights WEIGHTS` : Weights file for YOLO, e.g. [yolov3.weights](https://pjreddie.com/media/files/yolov3.weights).

`-c CONFIDENCE` : Minimum confidence to filter weak detections, default 0.5.

`-th THRESHOLD` : Threshold when applying non-maxima suppression, default 0.3.

For example, to use the pretrained YOLO model ([coco.names](https://github.com/pjreddie/darknet/blob/master/data/coco.names), [yolov3.cfg](https://github.com/pjreddie/darknet/blob/master/cfg/yolov3.cfg), and [yolov3.weights](https://pjreddie.com/media/files/yolov3.weights)) with plane_tracking.txt, download the files and run:

```
python viper_scraper.py yolo -d data_yolo_planes -t config/plane_tracking.txt -l 1000 --names yolo/coco.names --config yolo/yolov3.cfg --weights yolo/yolov3.weights -c .5 -th .3
```

## Scraping Instagram

```
python viper_scraper.py instagram ...
```

This script and associated utility scripts are based on Antonie Lin's non-API instagram scraper under the MIT license. Visit his (now-archived) repository at:

https://github.com/iammrhelo/InstagramCrawler

This is a non-API Instagram scraper using Selenium. As such, it is liable to break as Instagram changes their site. I will try to maintain its integrity but please feel free to contribute.

Scrape n images and associated captions from either a user or a hashtag.

**Before use**, run 

```
bash utils/get_gecko.sh
bash utils/get_phantomjs.sh
source utils/set_path.sh
```

**Usage**

```
viper_scraper.py instagram [-h] [-d DIR_PREFIX] [-q QUERY] [-n NUMBER] [-c caption] [-l Headless] [-a AUTHENTICATION] [-f FIREFOX_PATH]
```

`-d Directory Prefix` : The directory to save data to.

`-q QUERY` : The target (user or hashtag) to crawl. Add '#' for hashtags

`-n NUMBER` : The number of posts to download.

`-c Caption` : Add this flag to download captions when donaloading photos.

`-l headless` : If set, will use PhantomJS driver to run script as headless

`-a AUTHENTICATION` : Path to authentication JSON file - necessary for headless.

`f FIREFOX_PATH` : Path to the firefox installation for selenium.

#### Examples:

For example,

```
python viper_scraper.py instagram -d data_insta_test -q "#art" -c -n 100`
```

Will scrape the first 100 photos and captions from the art hashtag.
