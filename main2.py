import threading
import cv2
import socket
import time
import hashlib
import pickle

hashKey = hashlib.sha1("password".encode("utf-8")).hexdigest()
frame = None
exitFlag = 0
frameCaptureFailed = 0


threads = []

class CaptureImage(threading.Thread):
    '''Will run in a thread to capture images from the camera'''
    def __init__(self, name):
        threading.Thread.__init__(self)
        self.name = name

    def run(self):
        global exitFlag
        global frame
        global frameCaptureFailed
        cam = cv2.VideoCapture(0)
        while exitFlag == 0:
            retValue, tempFrame = cam.read()
            if not retValue:
                frameCaptureFailed = 1
                break
            
            # copy the frame into our global frame
            threadLock.acquire(1)
            frame = tempFrame
            threadLock.release()

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
            data = pickle.dumps(frame)
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
        
        print("Starting face detection")

        face_cascade = cv2.CascadeClassifier('./haarcascade_frontalface_alt.xml')
        while exitFlag == 0:
            if frame is not None:
                faces, faceRect = self.DetectFaces(face_cascade, frame)
 
                #Draw a rectangle around every found face
                threadLock.acquire(1)
                for (x,y,w,h) in faceRect:
                    cv2.rectangle(frame,(x,y),(x+w,y+h),(255,0,0),2)
                threadLock.release()


# So we can gain access to the frame object and not have issues writing to it and reading at the same time
threadLock = threading.Lock()

capImage = CaptureImage("ImageCapture")
capImage.start()

host = socket.gethostbyname(socket.gethostname())
port = 5995
print(host)
serverHost = StartServer("FrameServer", host, port)
serverHost.start()

faceDect = FaceDetect("Face Detection")
faceDect.start()


baseFrame = None

while True:
    try:
        if frame is not None:
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