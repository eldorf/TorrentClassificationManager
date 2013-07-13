import json
import logging
import httplib, urllib

def notifyRssFeed(torrentName):
    """Notify the Rss feed about the downloaded torrent."""

    host = "127.0.0.1"
    address = "/index.php?page=createfeed&action=create"

    title = "Torrent downloaded"
    category = "Torrent"
    description = "Torrent {0} has finished download.".format(torrentName)
    try:
	conn = httplib.HTTPSConnection(host)
        conn.connect()
    except httplib.HTTPException as e:
	logging.warning(e)
	return

    headers = {"Content-type": "application/x-www-form-urlencoded", "Accept": "text/plain"} 
    data = urllib.urlencode({'createTitle':title, 'createCategory':category, 'createDescription':description})
    conn.request("POST", address, data, headers)
    res = conn.getresponse()
    if res.status != httplib.OK:
       logging.warning("Rss response: {0} {1}".format(res.status, res.reason))
  
def notifyXbmcClients(torrentName):
    """Notify the xbmc clients about the downloaded torrent."""
    import socket, urllib, json

    addresses = ["192.168.1.60"]
    jsonPort = 9090
    for address in addresses:
        jsonAddress = (address, jsonPort)
        try:
            jsonSocket = socket.create_connection(jsonAddress)
            jsonSocket.settimeout(1)
        except socket.error:
            # No connection to the machine, ignore
            continue

        # Check if a player is used    
        command = '{ "jsonrpc": "2.0", "method": "Player.GetActivePlayers", "id": 1 }'
        jsonSocket.sendall(command)
        answer = jsonSocket.recv(1024)
        jsonAns = json.loads(answer)

        # Content in result means that some player is used
        # We do not not want to disturb that
        if jsonAns["result"]:
            jsonSocket.close()
            continue

        # Send the notification
        title = "Download complete"
        message = torrentName + " is downloaded."
        command = '{ "jsonrpc": "2.0", "method": "GUI.ShowNotification", "params": {"title":"' +title +'", "message":"' + message +'"}, "id": 1}'
        jsonSocket.sendall(command)
        answer = jsonSocket.recv(1024)
        jsonAns = json.loads(answer)
       
        jsonSocket.close()
 

# Test the notifications
if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    notifyRssFeed("This is just a test")
    notifyXbmcClients("This is just a test")
