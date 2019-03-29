import tweepy

class YoloStreamListener(tweepy.StreamListener):
    """
    Listen for data
    """
    def __init__(self, directory, api=None, limit=1000):
        super().__init__(api)
        self.directory = directory
        self.limit = 0
        self.cnt = 0

    def on_status(self, status):
        if status.text.startswith('RT'):
            return True # Ignore RTs to avoid repeat data
        try:
            with open(os.path.join(self.directory,'data.csv'), 'a+') as f:
                print("ciao")

        except OSError:
            print(str(OSError))
            print("On tweet " +str(self.cnt))
            return False 
        return True

    def on_error(self, status_code):
        if status_code == 420:
            #returning False in on_data disconnects the stream
            return False
        return False