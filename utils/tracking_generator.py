import pandas as pd
import numpy as np
import csv
import logging
import nltk
import os
import glob
import argparse
import json
from nltk.tokenize import TweetTokenizer
from sklearn.feature_extraction.text import TfidfVectorizer
from operator import itemgetter

def trending_phrases(csv_filename):
    """
    Get top 400 trending phrases from our data and saves in the topn.txt file
    """
    df = pd.read_csv(csv_filename)

    print(df.size)

    # Partition data - only want to analyze desirable set
    # TODO what?? why does it think axis is a parameter for is_above_threshold???????
    m = df['detected_file'].apply(is_above_threshold,args=[csv_filename,.5],)
    data_filtered = df[m]

    print(data_filtered.size)

    tokenizer = TweetTokenizer()
    vectorizer = TfidfVectorizer(tokenizer=tokenizer.tokenize,ngram_range=(1,2)) # One to two word phrases
    response = vectorizer.fit_transform(data_filtered['text'])    # Map feature index to feature name
    feature_names = vectorizer.get_feature_names()    #  weight is the tf-idf value
    weight = vectorizer.idf_
    #sorting the weights
    indices = np.argsort(weight)[::-1]
    top_weights = 400
    top_features = [feature_names[i] for i in indices[:top_weights]]
    with open('topn.txt', 'w') as f:
        for word in top_features:
            f.write(word + '\n')

# Returns true if the object has been detected with some confidence above
# the threshold in the image
def is_above_threshold(detected_filename, csv_filename, threshold):
    file_path = os.path.join(os.path.dirname(csv_filename),detected_filename)
    try:
        with open(file_path,'r') as f:
            detected = json.load(f)
            if len(detected['aeroplane']) is 0:
                return False
            else:
                for c in detected['aeroplane']:
                    if c > threshold:
                        return True
                return False
    except OSError as e:
        print(e)
        return False

if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    parser.add_argument('csv_file',metavar="CSV File",
                        help="The path to the csv file containing tweets")

    args = parser.parse_args()
    trending_phrases(args.csv_file)