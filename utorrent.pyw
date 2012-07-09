
import sys
import re
import os
import shutil
import time
from datetime import datetime
import logging

# --- Constants --- #
seriePath = "D:\\Film\\Serier\\"
moviePath = "D:\\Film\\Movies\\"
logFile = "D:\\Film\\utorrentScript.log"

#Setup logging format
logging.basicConfig(format="%(message)s", filename=logFile, filemode='a', level=logging.INFO)

#--- Classes --- #

# Class that checks if a filetype is valid Video type
class VideoFileTypes:
    types = {"avi", "mkv", "mov", "mp4", "mpg", "mpeg", "wmv"}
   
    @staticmethod
    def isVideoFile(filename):
        if filename is None:
            return False
            
        nameParts = filename.split('.')
        lastPart = nameParts.pop()
        if lastPart in VideoFileTypes.types:
            return True
        else:
            return False

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

# Class for specifying the type of a downloaded torrent        
class TorrentType:
    Video, Serie, Movie, Other = range(4)

    @staticmethod
    def decode(type):
        if TorrentType.Video == type:
            return "Video"
        elif TorrentType.Serie == type:
            return "Serie"
        elif TorrentType.Movie == type:
            return "Movie"
        else:
            return "Other"

# Class containing information about the torrent            
class Torrent:
    def __init__(self, argv):
        if len(argv) < 5 or len(argv) > 6:
            sys.exit(2)
            
        self.isDirectory = False
        self.isCompleteSeason = False
        self.name = "unknown"
        self.episode = None
        self.season = None
        self.torrentType = TorrentType.Other
        self.downloadPath = sys.argv[1]
        self.filename = sys.argv[2]
        self.status = int(sys.argv[3])
        self.state = sys.argv[4]
        self.isFinnished = False
        
        if len(argv) == 6:
            self.isFinnished = True

        self.fullPath = ""
        self.newPath = ""
    
    # Calculates the destination path    
    def calculateNewPath(self):
        if self.torrentType == TorrentType.Serie:
            self.newPath = os.path.join(seriePath, self.name, "Season {:0>2}".format(self.season))
        elif self.torrentType == TorrentType.Movie:
            self.newPath = os.path.join(moviePath, self.name)
    
    # Converts the filename to camelCase with spaces
    def checkNameSyntax(self):
        nameParts = self.name.split('.')
        
        newName = ""
        for part in nameParts:
            newName += part.capitalize() + " "

        self.name = newName.strip()

# Main class that makes all the torrent calculations        
class Matcher:
    # Entrance for calculating the torrent
    @staticmethod
    def parseTorrent(torrent):       
        if os.path.isfile(os.path.join(torrent.downloadPath, torrent.filename)):
            torrent.fullPath = os.path.join(torrent.downloadPath, torrent.filename)
            Matcher.parseFileName(torrent, torrent.filename)
        else:
            pathParts = torrent.downloadPath.split('\\')
            lastpart = pathParts.pop()
            if lastpart == torrent.filename and os.path.isdir(torrent.downloadPath):
                torrent.isDirectory = True
                torrent.fullPath = torrent.downloadPath
                filename = Matcher.retrieveFileName(torrent.downloadPath)
                Matcher.parseFileName(torrent, filename)
                Matcher.parseDirectoryName(torrent)
            else:
                message = "Downloaded file does not exist. Path: \"{}\" Name: \"{}\"\n".format(torrent.downloadPath, torrent.filename)
                logging.error(message)
                raise Exception(message)
                
    @staticmethod
    def parseFileName(torrent, filename):
        if VideoFileTypes.isVideoFile(filename):
            torrent.torrentType = TorrentType.Video
            Matcher.parseVideoTorrent(torrent, filename)
        else:
            torrent.torrentType = TorrentType.Other
    
    @staticmethod
    def parseVideoTorrent(torrent, filename):       
        result = Matcher.searchForSerieInName(filename)
        if result is not None and \
           int(result.group(2)) < 19: # If season is 19 or 20 its more likely its a year for a movie
            torrent.torrentType = TorrentType.Serie
            torrent.name = result.group(1)
            torrent.season = result.group(2)
            torrent.episode = result.group(3)
            
        else:
            torrent.torrentType = TorrentType.Movie
            torrent.name = torrent.filename

    @staticmethod
    def parseDirectoryName(torrent):
        assert(torrent.isDirectory)
        if torrent.torrentType != TorrentType.Serie:
            return
            
        result = Matcher.searchForSerieInName(torrent.filename)
        if result is None:
            torrent.isCompleteSeason = True
    
    @staticmethod
    def searchForSerieInName(filename):
        regexp = "(.*)\.S?(\\d{1,2})E?(\\d{2})\.(.*)"
        reObject = re.compile(regexp, re.IGNORECASE)
        return reObject.search(filename)
    
    @staticmethod    
    def retrieveFileName(inPath, firstTime = True):
        fileList = os.listdir(inPath)

        directories = []
        for file in fileList:
            reResult = re.search("sample", file, re.IGNORECASE)
            if reResult is not None:
                    continue
            if os.path.isdir(os.path.join(inPath, file)):
                directories.append(file)
            if VideoFileTypes.isVideoFile(file):
                return file  
        
        if firstTime:
            for dir in directories:        
                fileResult = Matcher.retrieveFileName(os.path.join(inPath, dir), False)
                if fileResult is not None:
                    return fileResult
        return None
        
def handleRmTreeError(function, path, exc_info):
    logging.error("{0}, {1}, {2}".format(function, path, exc_info))


def notifyXbmcClient(torrentName):
    import socket, urllib, json

    jsonPort = 9090
    address = "192.168.1.60"

    jsonAddress = (address, jsonPort)
    try:
        jsonSocket = socket.create_connection(jsonAddress)
    except socket.error:
        # No connection to the machine, ignore
        return

    # Check if a player is used    
    command = '{ "jsonrpc": "2.0", "method": "Player.GetActivePlayers", "id": 1 }'
    jsonSocket.sendall(command)
    answer = jsonSocket.recv(1024)
    jsonAns = json.loads(answer)

    jsonSocket.close()
    # Content in result means that some player is used
    # We do not not want to disturb that
    if jsonAns["result"]:
        return

    # Send the notification
    logging.debug("   Sending notification to Xbmc client")
    httpUserName = "xbmc"
    httpPassword = "4455"
    httpPort = 49750

    reqAddress = "{0}:{1}".format(address, httpPort )
    title = "Download complete"
    message = torrentName + " is downloaded."
    command = "/xbmcCmds/xbmcHttp?command=ExecBuiltIn&parameter=Notification({0},{1},10000)".format(title, message)
    req = reqAddress +command
    urllib.urlopen("http://" + httpUserName + ":" +httpPassword + "@" + req )

        
def main(argv):
    # --- Start script --- #            
    args = datetime.now().strftime("%Y-%m-%d %H:%M, ")
    for arg in argv:
        args += "\"" +arg +"\" "
    logging.info(args)

    torrent = Torrent(sys.argv)
    Matcher.parseTorrent(torrent)
    torrent.checkNameSyntax()
    torrent.calculateNewPath()

    logging.info("  Filename: {}".format(torrent.filename))
    logging.info("  Torrent type: {}".format(TorrentType.decode(torrent.torrentType)))
    logging.info("  isDirectory: {}".format(torrent.isDirectory))
    logging.debug("  Status: {} = {}".format(torrent.status, Status.decode(torrent.status)))
    if torrent.torrentType == TorrentType.Serie:
        logging.info("  Serie: {}".format(torrent.name))
        logging.info("  Season: {} ".format(torrent.season))
        if torrent.isCompleteSeason:
            logging.info("  Season Complete")        
        else:
            logging.info("  Episode: {}".format(torrent.episode))
    elif torrent.torrentType == TorrentType.Movie:
        logging.info("  Movie: {}".format(torrent.name))

    try:    
        if torrent.isDirectory:
            if not os.path.exists(torrent.newPath):
                logging.info("  Move from \"{}\" to \"{}\"".format(torrent.fullPath, torrent.newPath))
                shutil.move(torrent.fullPath, torrent.newPath)       
            else:
                logging.info("  Move from \"{}\" to existing directory \"{}\"".format(torrent.fullPath, torrent.newPath))
                # Move all the files and then remove the old directory
                for file in os.listdir(torrent.fullPath):
                    if file == "Thumbs.db": continue
                    shutil.move(os.path.join(torrent.fullPath,file), torrent.newPath)
                time.sleep(1) # To let windows release the lock on Thumbs.db
                shutil.rmtree(torrent.fullPath, False, handleRmTreeError)
        else:
            #Create destination directory if it does not exist
            if not os.path.exists(torrent.newPath):
                os.makedirs(torrent.newPath)
            
            newFile = os.path.join(torrent.newPath, torrent.filename)
            logging.info("  Move from \"{}\" to \"{}\"".format(torrent.fullPath, newFile))
            shutil.move(torrent.fullPath, newFile)
        notifyXbmcClient(torrent.name)

    except IOError as error:
        logging.error("IO Error({0})".format(error))
    except shutil.Error as error:
        logging.error("Shutil Error({})".format(error))
    except:
        logging.error("Unexpected error: {}".format(sys.exc_info()))
            
    logging.info("")

if __name__ == "__main__":
    try:
        main(sys.argv)  
    except Exception:
        import traceback
        logging.error(traceback.format_exc())
        sys.exit(2)  
