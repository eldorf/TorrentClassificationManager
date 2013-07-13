#!/usr/bin/env python
import sys, os
import subprocess
import shutil


torrentBaseDir = '/mnt/downloads/'

def createFile(fileName):
    filepath = os.path.join(torrentBaseDir, fileName)
    if not os.path.exists(filepath):
        file(filepath, "w").close()
    return filepath

def testTransmission():
    videoFileName = "testSerie.S01E14.someText.avi"
    filepath = createFile(videoFileName)
    os.environ["TR_APP_VERSION"] = "TransmissionTest1.0"
    os.environ["TR_TORRENT_DIR"] = torrentBaseDir
    os.environ["TR_TORRENT_NAME"] = videoFileName
    os.environ["TR_TORRENT_HASH"] = "thisIsTheHash"
    os.environ["TR_TORRENT_ID"] = "1234"


    
    os.chdir('..')
    command = ['./torrent.pyw', '--logToScreen'] 
    subprocess.check_call(command)

    serieBaseDir = os.path.join(torrentBaseDir, 'Serier', 'Testserie')
    expectedDestination = os.path.join(serieBaseDir, 'Season 01', videoFileName)
    if os.path.exists(expectedDestination):
        shutil.rmtree(serieBaseDir)
    else:
        print "Test FAILED!!"
        raise Exception("File has not been moved")

    if os.path.exists(filepath):
        print "Test Failed!!"
        raise Exception("Original file still exists")

    print "Test PASS!" 


def main(argv):

    testTransmission()





if __name__ == "__main__":
    main(sys.argv[1:])
