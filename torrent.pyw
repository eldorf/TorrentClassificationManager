#!/usr/bin/env python
import sys, re
import os, stat
import shutil
import time, glob
from datetime import datetime
import logging
import NotificationHandler

# --- Constants --- #
watchdirPath = '/mnt/downloads/watchdir/'
seriePath = "/mnt/downloads/Serier/"
moviePath = "/mnt/downloads/Movies/"
otherPath = "/mnt/downloads/Other/"
logFile = "/mnt/downloads/torrentScript.log"

#Setup logging format
logging.basicConfig(format="%(message)s", filename=logFile, filemode='a', level=logging.DEBUG)

#--- Classes --- #

class VideoFileTypes:
    """Class that checks if a filetype is valid Video type."""

    types = ["avi", "mkv", "mov", "mp4", "mpg", "mpeg", "wmv"]
   
    @staticmethod
    def isVideoFile(filename):
        """Return if file is a videofile."""
        if filename is None:
            return False
            
        nameParts = filename.split('.')
        lastPart = nameParts.pop()
        if lastPart in VideoFileTypes.types:
            return True
        else:
            return False


class TorrentType:
    """Class for specifying the type of a downloaded torrent."""

    Video, Serie, Movie, Other = range(4)

    @staticmethod
    def toString(type):
        """Return the type as a string."""
        if TorrentType.Video == type:
            return "Video"
        elif TorrentType.Serie == type:
            return "Serie"
        elif TorrentType.Movie == type:
            return "Movie"
        else:
            return "Other"

class Torrent:
    """Class containing information about the torrent."""

    def __init__(self, downloadPath, filename, id = None):
        self.isDirectory = False
        self.isCompleteSeason = False
        self.name = "unknown"
        self.episode = None
        self.season = None
        self.torrentType = TorrentType.Other
        self.downloadPath = downloadPath
        self.filename = filename
        self.id = id

        self.fullPath = ""
        self.newPath = ""

    def getName(self):
        """Return the name of the torrent."""
        if self.torrentType == TorrentType.Serie:
            if self.isCompleteSeason:
                return "{0} Season {1}".format(self.name, self.season)
            else:
                return "{0} S{1}E{2}".format(self.name, self.season, self.episode)
        else:
            return self.name
    
    def calculateNewPath(self):
        """Calculate the destination path for the torrent."""
        if self.torrentType == TorrentType.Serie:
            self.newPath = os.path.join(seriePath, self.name, "Season {:0>2}".format(self.season))
        elif self.torrentType == TorrentType.Movie:
            self.newPath = os.path.join(moviePath, self.name)
        else:
             self.newPath = os.path.join(otherPath, self.name)
    
    def checkNameSyntax(self):
        """Convert the filename to camelCase with spaces."""
        nameParts = self.name.split('.')
        
        newName = ""
        for part in nameParts:
            newName += part.capitalize() + " "

        self.name = newName.strip()

class Matcher:
    """Main class that makes all the torrent calculations."""

    @staticmethod
    def parseTorrent(torrent):       
    """Calculate the data from the torrent.

    The entrance function to begin the torrent calcualations.
    """
        if os.path.isfile(os.path.join(torrent.downloadPath, torrent.filename)):
            torrent.fullPath = os.path.join(torrent.downloadPath, torrent.filename)
            Matcher._parseFileName(torrent, torrent.filename)
        else:
            pathParts = torrent.downloadPath.split(os.sep)
            lastpart = pathParts.pop()
            if lastpart == torrent.filename and os.path.isdir(torrent.downloadPath):
                torrent.isDirectory = True
                torrent.fullPath = torrent.downloadPath
                filename = Matcher._retrieveFileName(torrent.downloadPath)
                Matcher._parseFileName(torrent, filename)
                Matcher._parseDirectoryName(torrent)
            else:
                message = "Downloaded file does not exist. Path: \"{}\" Name: \"{}\"\n".format(torrent.downloadPath, torrent.filename)
                logging.error(message)
                raise Exception(message)
                
    @staticmethod
    def _parseFileName(torrent, filename):
        """Find the type of the torrent"""
        if VideoFileTypes.isVideoFile(filename):
            torrent.torrentType = TorrentType.Video
            Matcher._parseVideoTorrent(torrent, filename)
        else:
            torrent.torrentType = TorrentType.Other
    
    @staticmethod
    def _parseVideoTorrent(torrent, filename):
        """Parse a video torrent to get name, season, episode etc."""
        result = Matcher._searchForSerieInName(filename)
        if result is not None and \
           int(result.group(2)) < 19 and \
           int(result.group(3)) < 30:
            # If season is 19 or 20 its more likely its a year for a movie
            # If episode is larger than 30 its more likely to be another type of number
            torrent.torrentType = TorrentType.Serie
            torrent.name = result.group(1)
            torrent.season = result.group(2)
            torrent.episode = result.group(3)
            
        else:
            torrent.torrentType = TorrentType.Movie
            torrent.name = torrent.filename

    @staticmethod
    def _parseDirectoryName(torrent):
        """Parse a directory to find if it contains a serie."""
        assert(torrent.isDirectory)
        if torrent.torrentType != TorrentType.Serie:
            return
            
        result = Matcher._searchForSerieInName(torrent.filename)
        if result is None:
            torrent.isCompleteSeason = True
    
    @staticmethod
    def _searchForSerieInName(filename):
        """Parse a filname to find a serie episode and season."""
        regexp = "(.*)\.S?(\\d{1,2})[Ex]?(\\d{2})\.(.*)"
        reObject = re.compile(regexp, re.IGNORECASE)
        return reObject.search(filename)
    
    @staticmethod    
    def _retrieveFileName(inPath, firstTime = True):
        """Go through the files in the torrent and look for a video file."""
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
                fileResult = Matcher._retrieveFileName(os.path.join(inPath, dir), False)
                if fileResult is not None:
                    return fileResult
        return None
        
def handleRmTreeError(function, path, exc_info):
    """Handle and print understandable error message at error from shutil.rmtree()."""
    logging.error("{0}, {1}, {2}".format(function, path, exc_info))


def getClient(argv):
    """Find out which and return the torrent client is used."""
    try:
        # Checking for transmission client
        trVersion = os.environ["TR_APP_VERSION"]
    except KeyError:
        trVersion = None

    if len(argv) == 4 or len(argv) == 5:
        logging.debug("Using uTorrent")
        from uTorrentSpecific import UTorrent
        return UTorrent(argv)
    elif len(argv) == 0 and trVersion != None:
        logging.debug("Using Transmission")
        from transmissionSpecific import Transmission
        return Transmission()
    else:
        logging.error("No valid client found")
        sys.exit(1)

def clearWatchdir(torrent):
    """Remove old torrent files in the watch directory."""
    if not watchdirPath:
        return
    result = glob.glob(os.path.join(watchdirPath, torrent.name)+'*')
    try:
        for rfile in result:
            logging.debug("   Removing file {}".format(rfile))
            os.remove(rfile)
    except OSError as error:
        logging.error("OS Error({0})".format(error))

def main(argv):
    # --- Start script --- #            
    args = datetime.now().strftime("%Y-%m-%d %H:%M, ")
    for arg in argv:
        args += "\"" +arg +"\" "
    logging.info(args)

    client = getClient(argv[1:])
    torrent = Torrent(*client.getTorrentInfo())
    Matcher.parseTorrent(torrent)
    torrent.checkNameSyntax()
    torrent.calculateNewPath()

    logging.info("  Filename: {}".format(torrent.filename))
    logging.info("  Filepath: {}".format(torrent.fullPath))
    logging.debug("  New path: {}".format(torrent.newPath))
    logging.info("  Torrent type: {}".format(TorrentType.toString(torrent.torrentType)))
    logging.info("  isDirectory: {}".format(torrent.isDirectory))
    if torrent.torrentType == TorrentType.Serie:
        logging.info("  Serie: {}".format(torrent.name))
        logging.info("  Season: {} ".format(torrent.season))
        if torrent.isCompleteSeason:
            logging.info("  Season Complete")        
        else:
            logging.info("  Episode: {}".format(torrent.episode))
    elif torrent.torrentType == TorrentType.Movie:
        logging.info("  Movie: {}".format(torrent.name))
    else:
        logging.debug("  Other formats is not handled")
        logging.info("")
    
    try:    
        if torrent.isDirectory:
            if not os.path.exists(torrent.newPath):
                logging.debug("  Createing directory \"{}\"".format(torrent.newPath))
                os.makedirs(torrent.newPath)
            logging.info("  Move from \"{}\" to existing directory \"{}\"".format(torrent.fullPath, torrent.newPath))
            downloadComplete = True
            # Move all the files and then remove the old directory
            for file in os.listdir(torrent.fullPath):
                if file == "Thumbs.db":
                     continue
                if ".part" in file:
                    # Not all part are done, leaving those
                    downloadComplete = False
                    continue
                shutil.move(os.path.join(torrent.fullPath,file), torrent.newPath)
            if downloadComplete:
                logging.debug("  Download complete, removing directory \"{}\"".format(torrent.fullPath))
                time.sleep(1) # To let windows release the lock on Thumbs.db
                shutil.rmtree(torrent.fullPath, False, handleRmTreeError)
        else:
            #Create destination directory if it does not exist
            if not os.path.exists(torrent.newPath):
                os.makedirs(torrent.newPath)
            newFile = os.path.join(torrent.newPath, torrent.filename)
            logging.info("  Move from \"{}\" to \"{}\"".format(torrent.fullPath, newFile))
            shutil.move(torrent.fullPath, newFile)
            
            # Only transmission supports updating the path
            if client.getClientName() == "transmission":
                client.updatePath(torrent.id, torrent.newPath)

        clearWatchdir(torrent)
                
        NotificationHandler.notifyRssFeed(torrent.getName())
        NotificationHandler.notifyXbmcClients(torrent.getName())

    except IOError as error:
        logging.error("IO Error({0})".format(error))
	raise
    except shutil.Error as error:
        logging.error("Shutil Error({})".format(error))
	raise
            
    logging.info("")

if __name__ == "__main__":
    try:
        main(sys.argv)  
    except Exception:
        import traceback
        var = traceback.format_exc()
        logging.error(var)
        logging.info("")
        sys.exit(2)  
