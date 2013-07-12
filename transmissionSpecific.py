import os, httplib, json, logging, random

class Transmission:
    """Class that handles transmission communication."""
    def __init__(self):
        self.port = 9091
        self.host = "127.0.0.1"
        self.path = "/transmission/rpc/"
        self.tag = random.randint(1, 10000)
        self.connection = None
        self.headers = ""
        
        try:
            self.version = os.environ["TR_APP_VERSION"]
            self.downloadPath = os.environ["TR_TORRENT_DIR"]
            self.torrentName = os.environ["TR_TORRENT_NAME"]
            self.localtime = os.environ["TR_TIME_LOCALTIME"]
            self.torrentHash = os.environ["TR_TORRENT_HASH"]
            self.torrentId = int(os.environ["TR_TORRENT_ID"])
            if os.sep == '\\':            
                self.downloadPath = self.downloadPath.replace("/", "\\")
            fullpath = os.path.join(self.downloadPath, self.torrentName)
            if not os.path.isfile(fullpath) and os.path.isdir(fullpath):
                # Add the downloaded directory to download path to mimic the behavior of utorrent
                self.downloadPath = fullpath        
        except KeyError as e:
            logging.error("Unable to retrive Transmission data: {0}".format(e))
            sys.exit(1)

    def __del__(self):
        if self.connection:
            self.connection.close()
            
            
    def retrieveHeader(self):
        """Retrieving and return the session id"""
        conn = httplib.HTTPConnection(self.host, self.port)
        conn.request("GET", self.path)
        response = conn.getresponse()
        response_data = response.read()
        response.close()
        conn.close()
        session_id = str(response_data).split("X-Transmission-Session-Id: ")[-1][0:1-len("</code></p>'")]
        return {'x-transmission-session-id': str(session_id)}
            
    def getTorrentInfo(self):
        """Return the torrent info."""
        return [self.downloadPath, self.torrentName, self.torrentId]
        
    def getClientName(self):
        """Return the name of the client."""
        return "transmission"
        
    def _sendRequest(self, command):
        """Send request to the transmission daemon."""
        if self.connection == None:
            self.connection = httplib.HTTPConnection(self.host, self.port)
            self.headers = self.retrieveHeader()
            self.connection.request("POST", self.path, command, self.headers)

            response = self.connection.getresponse()
            response_raw = response.read()
            response.close()
            #conn.close()

        self.connection.request("POST", self.path, command, self.headers)
        response = self.connection.getresponse()
        response_raw = response.read()
        response.close()
            
        response = json.loads(response_raw.decode("utf-8"))
        return response

    def _checkResponseOk(self, response):
        """Return if the response has a success result."""
        try:
            if response["result"] != "success":
               return False
        except KeyError:
           
            return False
        return True
        
    def updatePath(self, id, newPath):
        """Tells transmission to update the path to the torrent."""
        command = json.dumps({ "arguments": { "location": newPath, "ids": [id] }, "method": "torrent-set-location", "tag": self.tag })
        
        response = self._sendRequest(command)
        if not self._checkResponseOk(response):
            logging.warning("Unable to update the address in transmission")
            return
            
        command = json.dumps({ "arguments": { "ids": [id]}, "method": "torrent-verify", "tag": self.tag })
       
        response = self._sendRequest(command)
        if not self._checkResponseOk(response):
            logging.warning("Unable to verify the new address in transmission")
            return

