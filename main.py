import threading
import cv2
import socket
import time
import hashlib
import pickle
from subprocess import check_output 
from sys import platform
import imp
import getpass

#To allow either Windows or Raspbian, we'll test to make sure the modules required are found first.
try:
    imp.find_module('picamera')
    imp.find_module('picamera.array')
    from picamera.array import PiRGBArray
    from picamera import PiCamera
    piCameraFound = True
except ImportError:
    piCameraFound = False


# need a reliable way to get the current host address to bind to
if platform == "linux" or platform == "linux2":
    host = check_output(['hostname', '-I']) #need to get the wlan0 host IP otherwise it returns 127.0.0.1
elif platform == "win32":
    host = socket.gethostbyname(socket.gethostname())

port = 5995

frame = None
exitFlag = 0
frameCaptureFailed = 0
threads = []
faceRect = None

class CaptureImage(threading.Thread):
    '''Will run in a thread to capture images from the camera'''
    def __init__(self, name):
        threading.Thread.__init__(self)
        self.name = name

    def run(self):
        global exitFlag
        global frame
        global frameCaptureFailed

        # If no picamera module, we won't ask, just load the usb camera
        if not piCameraFound:
            whichCamera = 2
        else:
            whichCamera = int(input("Please enter 1 for PiCamera and 2 for USB Camera: "))

        if whichCamera == 1:
            camera = PiCamera()
            camera.resolution = (640, 480)
            camera.framerate = 32
            rawCapture = PiRGBArray(camera, size=(640, 480))

            for frame in camera.capture_continuous(rawCapture, format="bgr", use_video_port=True):
                
                if exitFlag == 1:
                    break

                tempFrame = frame.array

                # clear the stream in preparation for the next frame
                rawCapture.truncate(0)

                # copy the frame into our global frame
                threadLock.acquire(1)
                frame = tempFrame
                threadLock.release()
        elif whichCamera == 2:
            camera = cv2.VideoCapture(0)               
            while exitFlag == 0:

                retValue, tempFrame = camera.read()
                if not retValue:
                    frameCaptureFailed = 1
                    break

                # copy the frame into our global frame
                threadLock.acquire(1)
                frame = tempFrame
                threadLock.release()
        else:
            print("Invalid entry! Closing")
            frameCaptureFailed = 1

class StartFrameServer(threading.Thread):
    '''This is the server that sends the frames out as TCP packets'''
    def __init__(self, name, addr):
        threading.Thread.__init__(self)
        self.name = name
        self.addr = addr
    
    def run(self):
        global frame
        global exitFlag

        serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        serverSocket.connect((self.addr[0], 5996))
        while exitFlag == 0: 
            # pickle is a serialiser -> encodes it as bytes for sending over the network
            data = pickle.dumps(frame, protocol=2)
            frameLength = str(len(data))
            message = ("Frame=" + frameLength.zfill(8)).encode("utf-8")
            #serverSocket.send(message)
            serverSocket.sendall(message + data)
            time.sleep(0.1)

class StartServer(threading.Thread):
    '''This will start a server to capture incomming connections and ensure they are valid'''
    def __init__(self, name, host, port):
        threading.Thread.__init__(self)
        self.name = name
        self.host = host
        self.port = port

    def handleData(self, data, addr):
        global hashKey
        global threads
        
        if data:
            if data == hashKey:
                print("Authenticated")
                frameServer = StartFrameServer("frameServer", addr)
                frameServer.start()
                threads.append(frameServer)
            else:
                print("Invalid token!")

    def run(self):
        global frame
        global exitFlag
        serverSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        serverSocket.settimeout(1.0)
        serverSocket.bind((self.host, self.port))

        while exitFlag == 0:
            try:
                data, addr = serverSocket.recvfrom(1024)
                print("Connected to: ", addr)
                self.handleData(data.decode(), addr)
            except socket.timeout:
                pass

class FaceDetect(threading.Thread):
    def __init__(self, name):
        threading.Thread.__init__(self)
        self.name = name

    def DetectFaces(self, faceCascade, frame):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY) 
        faceRect = faceCascade.detectMultiScale(gray, 1.1, 5)
        return [gray[y:y+w, x:x+h] for (x,y,w,h) in faceRect], faceRect

    def run(self):
        global frame
        global exitFlag
        global faceRect
        
        print("Starting face detection")

        face_cascade = cv2.CascadeClassifier('./haarcascades/haarcascade_frontalface_alt.xml')
        while exitFlag == 0:
            if frame is not None:
                faces, faceRect = self.DetectFaces(face_cascade, frame)
 

# So we can gain access to the frame object and not have issues writing to it and reading at the same time
threadLock = threading.Lock()

# Start Server to listen for broadcast requests
print(host)
serverHost = StartServer("FrameServer", host, port)
serverHost.start()

# Start frame capture
capImage = CaptureImage("ImageCapture")
capImage.start()

# Start detecting faces in those frame
faceDect = FaceDetect("Face Detection")
faceDect.start()

# We can include something to allow changing the password on startup
password = getpass.getpass("Please enter server password: ")
hashKey = hashlib.sha256(password.encode("utf-8")).hexdigest()  #we can modify this later

while True:
    try:
        if frame is not None:
            if faceRect is not None:
                #Draw a rectangle around every found face
                for (x,y,w,h) in faceRect:
                    cv2.rectangle(frame,(x,y),(x+w,y+h),(255,0,0),2)
                    
            cv2.imshow("Server View", frame)

        key = cv2.waitKey(1)

        if key % 256 == 27:
            # ESC pressed
            print("Escape hit, closing...")
            break
        
        if frameCaptureFailed:
            print("Capture failed. Exiting")
            break
    except Exception as ex:
        print(ex)
        break

exitFlag = 1

# main servers
capImage.join()
serverHost.join()
faceDect.join()

#frame servers
for t in threads:
    t.join()