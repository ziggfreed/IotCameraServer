import socket
import hashlib
import cv2
import threading
import pickle
import time
import getpass
import commonCrypto

exitFlag = 0

frame = None
drawFrame = None
serverFailed = 0
debugFrame = None
frameContours = None
faceRect = None
faceCount = 0

# Crypto Stuff
privateKey, publicKey = commonCrypto.generate_keys_RSA()
assymetricKey = None

def main():
    global privateKey
    global assymetricKey

    host = "fe80::211c:dfe4:ba7f:4533%9"
    port = 5995

    password = getpass.getpass("Please enter password: ")

    clientSocket = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
    message = hashlib.sha256(password.encode("utf-8")).hexdigest()

    # clientSocket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    clientSocket.sendto(message.encode(), (host, port))

    #send the public key
    keyEncoded = publicKey.export_key(format="PEM")
    clientSocket.sendto(keyEncoded, (host, port))

    #So we don't endlessly loop
    clientSocket.settimeout(10)
    # read the sent message back
    dataRec = clientSocket.recv(2048)

    assymetricKey = commonCrypto.decrypt_message_RSA(dataRec, privateKey)

    #debug only!
    print(assymetricKey)

class FrameReceiverClient(threading.Thread):
    '''Gets those frames being sent down'''
    def __init__(self, name):
        threading.Thread.__init__(self)
        self.name = name
    
    def run(self):
        global frame
        global exitFlag
        global serverFailed

        recSocket = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)

        serverHost = "fe80::211c:dfe4:ba7f:4533%9"
        serverPort = 5996

        print("Binding to address: ", serverHost)

        recSocket.bind((serverHost, serverPort))

        recSocket.settimeout(10.0)
        recSocket.listen(1)

        try:
            conn, addr = recSocket.accept()
            print(addr, "has initiated a connection")
        except socket.timeout:
            serverFailed = 1
            return 

        recSocket.settimeout(1.0)

        while exitFlag == 0:
            try:
                # Get the frame length first
                messageType = conn.recv(5)  #what we're sending. Usually its just "Frame"
                equalSign = conn.recv(1)    #The = sign
                messageLength = int(conn.recv(8).decode("utf-8"))
                
                #AES stuff
                tag = conn.recv(16)
                nonce = conn.recv(16)

                # Don't always get a full frame in one read, might need to loop a few to ensure we get the full payload
                byteFrame = conn.recv(messageLength)
                while (len(byteFrame) < messageLength):
                    diff = messageLength - len(byteFrame)
                    newRead = conn.recv(diff)
                    byteFrame += newRead

                try:
                    #decode the frame
                    frameDecoded = commonCrypto.decrypt_message_AES(byteFrame, assymetricKey, nonce, tag)

                    #deserialise the frame from bytes
                    tempFrame = pickle.loads(frameDecoded, encoding="bytes")

                    threadLock.acquire(1)
                    frame = tempFrame
                    threadLock.release()
                except pickle.UnpicklingError:
                    print("Failed unpickling")
                    pass
                except Exception as ex:
                    print(ex)

            except socket.timeout:
                pass
            except Exception as ex:
                print(ex)
                serverFailed = 1
                break

        conn.close()

class MotionDetection(threading.Thread):
    def __init__(self, name):
        threading.Thread.__init__(self)
        self.name = name
    
    def run(self):
        global frame
        global drawFrame
        global debugFrame
        global frameContours

        baseFrame = None

        startTime = time.time()
        while exitFlag == 0:

            try:
                if frame is None:
                    continue

                drawFrame = cv2.resize(frame, (0,0), fx=0.5, fy=0.5) 
                workingFrame = cv2.cvtColor(drawFrame, cv2.COLOR_BGR2GRAY)
                workingFrame = cv2.GaussianBlur(workingFrame, (21, 21), 0)

                #What we compare against
                if baseFrame is None or time.time() > startTime + 10.0:  #refresh base image every few seconds. This can account for light changes throughout a day
                    baseFrame = workingFrame
                    startTime = time.time()

                #cv2.imshow("baseFrame", baseFrame)


                frameDifference = cv2.absdiff(baseFrame, workingFrame)
                debugFrame = frameDifference

                thresh = cv2.threshold(frameDifference, 25, 255, cv2.THRESH_BINARY)[1]
                #cv2.imshow("thresh", thresh)
                thresh = cv2.dilate(thresh, None, iterations=2)
                #cv2.imshow("thresh", thresh)
                im2, frameContours, hierarchy = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            except Exception as ex:
                print(ex)
                break

class FaceDetect(threading.Thread):
    def __init__(self, name):
        threading.Thread.__init__(self)
        self.name = name

    def DetectFaces(self, faceCascade, frame):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY) 
        faceRect = faceCascade.detectMultiScale(gray, scaleFactor = 1.1, minNeighbors = 10)
        return [gray[y:y+w, x:x+h] for (x,y,w,h) in faceRect], faceRect

    def run(self):
        global frame
        global exitFlag
        global faceRect
        global faceCount
        
        print("Starting face detection")

        face_cascade = cv2.CascadeClassifier('./haarcascades/haarcascade_frontalface_alt.xml')
        while exitFlag == 0:
            if frame is not None:
                faces, faceRect = self.DetectFaces(face_cascade, frame)

                # Uncomment if you want to save people's faces to the saved_faces folder
                # if faceRect is not None:
                #     # save them faces!
                #     for rect in faceRect:
                #         faceCount = faceCount + 1
                #         cv2.imwrite("./saved_faces/face" + str(faceCount) + ".png", frame[rect[1]:rect[1] + rect[2], rect[0] : rect[0] + rect[3]])
 

main()

threadLock = threading.Lock()

frameThread = FrameReceiverClient("inFrames")
frameThread.start()

motionDect = MotionDetection("motionDetection")
motionDect.start()

# Start detecting faces in those frame
faceDect = FaceDetect("Face Detection")
faceDect.start()

while True:
    #Draw the contours
    if frameContours is not None:

        if faceRect is not None:
            #Draw a rectangle around every found face
            for (x,y,w,h) in faceRect:
                cv2.rectangle(frame,(x,y),(x+w,y+h),(255,0,0),2)

        for c in frameContours:
            if cv2.contourArea(c) < 700:
                continue
            (x, y, w, h) = cv2.boundingRect(c)
            cv2.rectangle(drawFrame, (x, y), (x + w, y + h), (0, 255, 0), 2)

    if drawFrame is not None:
        cv2.imshow("Client View", drawFrame)
    
    if debugFrame is not None:
        cv2.imshow("debugFrame", debugFrame)

    key = cv2.waitKey(1)

    if key % 256 == 27:
        # ESC pressed
        print("Escape hit, closing...")
        break
    
    if serverFailed:
        print("server failed")
        break

exitFlag = 1

frameThread.join()
motionDect.join()
faceDect.join()