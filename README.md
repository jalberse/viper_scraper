# Viper Scraper

Scraping and ingesting multi-model data from online social networks

## Use

Before using any script, run `pipenv shell` to enter the virtual environment.

### Scraping Twitter

```
python viper_scraper.py twitter ...
```

Using the Twitter scraper requires registering as a Twitter developer and providing authentication keys. Place your keys in either *.my_keys* (in .gitignore) or *config/keys.json*

```
python viper_scraper.py twitter [-h] [-n Number] [-t Tracking File] [-d Directory Prefix] [--photo_limit] [--status_limit]
```

`-n Number` : The number of tweets (--status_limit flag) or images (--photo_limit flag, default) to scrape. Script will terminate when this number is reached.

`-t Tracking File` : The path to the tracking file. This file contains a list of phrases, one per line, used to filter the Twitter stream. See [Filter realtime Tweets](https://developer.twitter.com/en/docs/tweets/filter-realtime/guides/basic-stream-parameters.html) for more information or see config/plane_tracking.txt for an example.

`-d Directory Prefix` : The directory to save data to.

The Twitter scraper filters realtime tweets using the [Twitter API](https://developer.twitter.com/en/docs.html). Text, metadata, and references to donwloaded images are stored in data.csv under the specified directory.

### YOLO integration with Twitter

```
python viper_scraper.py yolo ...
```

The VIPER scraper also integrates [YOLO](https://pjreddie.com/darknet/yolo/) (You Only Look Once) real-time object detection.

For each tweet that passes the filter, the scraper will:

1. Download the original image
2. Save a version of the image with bounding boxes and predictions labelled
3. Save a .json file containing the confidences for each class
4. Save text and metadata, along with references to these files, in data.csv under the specified directory

Note that unlike the basic Twitter scraper, this script only saves tweets containing images.

```
python viper_scraper.py yolo [-h] [-d Data Directory] [-t Tracking File] [-n NUMBER] --names NAMES --config CONFIG --weights WEIGHTS [-c CONFIDENCE] [-th THRESHOLD]
```

`-d Directory Prefix` : The directory to save data to.

`-t Tracking File` : The path to the tracking file. This file contains a list of phrases, one per line, used to filter the Twitter stream. See [Filter realtime Tweets](https://developer.twitter.com/en/docs/tweets/filter-realtime/guides/basic-stream-parameters.html) for more information or see config/plane_tracking.txt for an example.

`-n NUMBER` : The number of images to scrape.

`--names NAMES` : A file containing the names, one per line, associated with the weights and config file for YOLO, e.g. [coco.names](https://github.com/pjreddie/darknet/blob/master/data/coco.names).

`--config CONFIG` : Config file for YOLO, e.g. [yolov3.cfg](https://github.com/pjreddie/darknet/blob/master/cfg/yolov3.cfg).

`--weights WEIGHTS` : Weights file for YOLO, e.g. [yolov3.weights](https://pjreddie.com/media/files/yolov3.weights).

`-c CONFIDENCE` : Minimum confidence to filter weak detections, default 0.5.

`-th THRESHOLD` : Threshold when applying non-maxima suppression, default 0.3.

#### YOLO Example

For example, to use the pretrained YOLO model ([coco.names](https://github.com/pjreddie/darknet/blob/master/data/coco.names), [yolov3.cfg](https://github.com/pjreddie/darknet/blob/master/cfg/yolov3.cfg), and [yolov3.weights](https://pjreddie.com/media/files/yolov3.weights)) with plane_tracking.txt, download the files and run:

```
python viper_scraper.py yolo -d data_yolo_test -t config/plane_tracking.txt -n 1000 --names coco.names --config yolov3.cfg --weights yolov3.weights -c .5 -th .3
```

### Tracking file generation

```
python utils/tracking_generator.py [CSV]
```

*This functionality is currently under development, see utils/tracking_generator.py*

The tracking_generator.py script takes the CSV and data obtained by running `viper_scraper.py yolo` and generates a tracking file for future use. 

For example, say that we are scraping for pictures of airplanes. We might start with a tracking file containing phrases such as "flying", "airplane", "travel", etc. The script partitions the resultant data into tweets which contain a picture of an airplane (YOLO detected at least one airplane above some confidence threshold) and those that do not. It takes the first partition and ranks phrases in the body of the tweets by TF-IDF score. The top n are placed into the new tracking file.

The data obtained using the new tracking file will (hopefully) have a higher ratio and volume of pictures of airplanes, as the phrases are known to be associated with desirable photos.

### Scraping Instagram

```
python viper_scraper.py instagram ...
```

This script and associated utility scripts are based on Antonie Lin's non-API instagram scraper under the MIT license. Visit his repository at:

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
