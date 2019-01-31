from setuptools import setup

with open("README.md", 'r') as f:
    long_description = f.read()

setup(
   name='viper_scraper',
   version='0.1.0',
   description='Scrape and ingest multi-model data',
   license="MIT",
   long_description=long_description,
   author='John Alberse',
   author_email='John.R.Alberse-1@ou.edu',
   url="https://github.com/jalberse/viper_scraper",
   packages=['viper_scraper'],  #same as name
   install_requires=['tweepy'], #external packages as dependencies
   scripts=[
            'scripts/vscraper.py',
           ]
)