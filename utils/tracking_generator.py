import pandas as pd
import numpy as np
import csv
import logging
import nltk
import os
import glob
import argparse
import json
import sys
from nltk.tokenize import TweetTokenizer
from sklearn.feature_extraction.text import TfidfVectorizer
from operator import itemgetter

def trending_phrases(csv_filename):
    """
    Get top 400 trending phrases from our data and saves in the topn.txt file
    """
    df = pd.read_csv(csv_filename)

    print(str(df.size) + " Total tweets")

    # Partition data - only want to analyze desirable set
    # m is bools
    m = df['detected_file'].apply(is_above_threshold,args=[csv_filename,.5],)
    
    # Remove URLs (links to images) or else they dominate ranking
    # Remove special chars (less # and @)
    data_filtered = df[m].replace('https?:\/\/.*[\r\n]*|[^0-9a-zA-Z#@]+',' ',regex=True)
    
    data_filtered.to_csv('ah')

    print(str(data_filtered.size) + " contain target")

    tokenizer = TweetTokenizer()
    # Override the tokenizer of the tfidfvectorizer with one made for tweets
    vectorizer = TfidfVectorizer(tokenizer=tokenizer.tokenize,ngram_range=(1,2)) # One to two word phrases
    # Get term-document matrix from tweets' text
    tdmat = vectorizer.fit_transform(data_filtered['text'])
    feature_names = vectorizer.get_feature_names()
    weight = vectorizer.idf_
    # Indices which would sort weights
    indices = np.argsort(weight)[::-1]
    n = 400
    # Grab top n features
    top_features = [feature_names[i] for i in indices[:n]]
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

# TODO: Actually let choose what we are looking for and confidence threshold
if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    parser.add_argument('csv_file',metavar="CSV File",
                        help="The path to the csv file containing tweets")

    args = parser.parse_args()
    trending_phrases(args.csv_file)