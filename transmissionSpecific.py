import os

class Transmission:
    def __init__(self):
        try:
            self.version = os.environ["TR_APP_VERSION"]
            self.downloadPath = os.environ["TR_TORRENT_DIR"]
            self.torrentName = os.environ["TR_TORRENT_NAME"]
            self.localtime = os.environ["TR_TIME_LOCALTIME"]
            self.torrentHash = os.environ["TR_TORRENT_HASH"]
            self.torrentId = os.environ["TR_TORRENT_ID"]
            
            
            self.downloadPath = self.downloadPath.replace("/", "\\")
            fullpath = os.path.join(self.downloadPath, self.torrentName)
            if not os.isfile(fullpath) and os.isdir(fullpath):
                # Add the downloaded directory to download path to mimic the behavior of utorrent
                self.downloadPath = fullpath        
        except KeyError as e:
            logging.error("Unable to retrive Transmission data: {0}".format(e))
            sys.exit(1)

    def getTorrentInfo(self):
        return [self.downloadPath, self.torrentName]
        
    def getClientName():
        return "transmission"
