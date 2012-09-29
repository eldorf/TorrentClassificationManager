import os, httplib, json, logging, random

class Transmission:
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
        # retrieving session id
        conn = httplib.HTTPConnection(self.host, self.port)
        conn.request("GET", self.path)
        response = conn.getresponse()
        response_data = response.read()
        response.close()
        conn.close()
        logging.debug("responseData: " + response_data)
        session_id = str(response_data).split("X-Transmission-Session-Id: ")[-1][0:1-len("</code></p>'")]
        return {'x-transmission-session-id': str(session_id)}
            
    def getTorrentInfo(self):
        return [self.downloadPath, self.torrentName, self.torrentId]
        
    def getClientName(self):
        return "transmission"
        
    def sendRequest(self, command):
        if self.connection == None:
            self.connection = httplib.HTTPConnection(self.host, self.port)
            self.headers = self.retrieveHeader()
            logging.debug("sending command: " + command + "header: " + str(self.headers))
            self.connection.request("POST", self.path, command, self.headers)

            response = self.connection.getresponse()
            response_raw = response.read()
            response.close()
            #conn.close()

        self.connection.request("POST", self.path, command, self.headers)
        response = self.connection.getresponse()
        response_raw = response.read()
        response.close()
            
        logging.debug("raw answer: " + response_raw)
        response = json.loads(response_raw.decode("utf-8"))
        return response

    def checkResponseOk(self, response):
        try:
            if response["result"] != "success":
               return False
        except KeyError:
           
            return False
        return True
        
    def updatePath(self, id, newPath):
        #command = json.dumps({ "arguments": { "fields": [ "id", "name", "totalSize" ], "ids": [id] }, "method": "torrent-get", "tag": self.tag })
        command = json.dumps({ "arguments": { "location": newPath, "ids": [id] }, "method": "torrent-set-location", "tag": self.tag })
        
        response = self.sendRequest(command)
        logging.debug("answer: " + json.dumps(response, indent=4))
        if not self.checkResponseOk(response):
            logging.warning("Unable to update the address in transmission")
            return
            
        command = json.dumps({ "arguments": { "ids": [id]}, "method": "torrent-verify", "tag": self.tag })
        logging.debug("sending command: " + command + "header: " + str(self.headers))
       
        response = self.sendRequest(command)
        logging.debug("answer: " + json.dumps(response, indent=4))
        if not self.checkResponseOk(response):
            logging.warning("Unable to verify the new address in transmission")
            return

