import socket
import hashlib
import cv2
import threading
import pickle
import time
import getpass

exitFlag = 0

frame = None
drawFrame = None
serverFailed = 0
debugFrame = None
frameContours = None

def main():
    host = "192.168.2.2"
    port = 5995

    password = getpass.getpass("Please enter password: ")

    clientSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    message = hashlib.sha256(password.encode("utf-8")).hexdigest()

    # clientSocket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    clientSocket.sendto(message.encode(), (host, port))

class FrameReceiverClient(threading.Thread):
    '''Gets those frames being sent down'''
    def __init__(self, name):
        threading.Thread.__init__(self)
        self.name = name
    
    def run(self):
        global frame
        global exitFlag
        global serverFailed

        recSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        serverHost = socket.gethostbyname(socket.gethostname())
        serverHost = "192.168.2.3"
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
                # Don't always get a full frame in one read, might need to loop a few to ensure we get the full payload
                byteFrame = conn.recv(messageLength)
                while (len(byteFrame) < messageLength):
                    diff = messageLength - len(byteFrame)
                    newRead = conn.recv(diff)
                    byteFrame += newRead

                try:
                    #deserialise the frame from bytes
                    tempFrame = pickle.loads(byteFrame, encoding="bytes")

                    threadLock.acquire(1)
                    frame = tempFrame
                    threadLock.release()
                except Exception as ex:
                    print(ex)

            except socket.timeout:
                pass
            except pickle.UnpicklingError:
                print("Failed unpickling")
                pass
            except Exception as ex:
                print(ex)
                serverFailed = 1
                break

        conn.close()

class ProcessFrame(threading.Thread):
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


main()

threadLock = threading.Lock()

frameThread = FrameReceiverClient("inFrames")
frameThread.start()

frameProcessor = ProcessFrame("frameProcessor")
frameProcessor.start()

while True:
    #Draw the contours
    if frameContours is not None:
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
frameProcessor.join()