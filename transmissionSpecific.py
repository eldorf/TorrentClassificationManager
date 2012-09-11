import os

class Transmission:
    def __init__(self):
        try:
            self.version = os.environ["TR_APP_VERSION"]
            self.downloadPath = os.environ["TR_TORRENT_DIR"]
            self.filename = os.environ["TR_TORRENT_NAME"]
        except KeyError as e:
            logging.error("Unable to retrive Transmission data: {0}".format(e))
            sys.exit(1)

    def getTorentInfo():
        return [self.downloadPath, self.filename]
