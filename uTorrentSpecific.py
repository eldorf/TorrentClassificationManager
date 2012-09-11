class UTorrent:
    def __init__(self, argv):
        if len(argv) < 3:
            logging.error("Unable to retrive uTorrentData")
            sys.exit(2)
        self.downloadPath = sys.argv[0]
        self.filename = sys.argv[1]
        self.status = int(sys.argv[2])

    def getTorrentInfo():
        return [self.downloadPath, self.filename] 


# Class for uTorrent status flags
class Status:
    Started = 1
    Checking = 2
    StartAfterCheck = 4 
    Checked = 8
    Error = 16
    Paused = 32
    Queued = 64
    Loaded = 128
    
    @staticmethod
    def decode(status):
        s = ""
        if (status & Status.Started):
            s += "Started | "
        if (status & Status.Checking):
            s += "Checking | "
        if (status & Status.StartAfterCheck):
            s += "StartAfterCheck | "
        if (status & Status.Checked):
            s += "Checked | "
        if (status & Status.Error):
            s += "Error | "
        if (status & Status.Paused):
            s += "Paused | "
        if (status & Status.Queued):
            s += "Queued | "
        if (status & Status.Loaded):
            s += "Loaded"
        
        return s

