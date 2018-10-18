import io
import cv2
import numpy

#Now creates an OpenCV image
cam = cv2.VideoCapture(0)
#Load a cascade file for detecting faces
defaulCascade = cv2.CascadeClassifier('./haarcascades/haarcascade_frontalface_default.xml')
eyesCascade = cv2.CascadeClassifier('./haarcascades/haarcascade_eye.xml')
# altCascade = cv2.CascadeClassifier('./haarcascades/haarcascade_frontalface_alt.xml')
# alt2Cascade = cv2.CascadeClassifier('./haarcascades/haarcascade_frontalface_alt2.xml')
# altTreeCascade = cv2.CascadeClassifier('./haarcascades/haarcascade_frontalface_alt_tree.xml')

def DetectFaces(cascade, frame):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY) 
    faceRect = cascade.detectMultiScale(gray, 1.1, 5)
    return [gray[y:y+w, x:x+h] for (x,y,w,h) in faceRect], faceRect

while True:
    try:
        retVal, image = cam.read()
        faces, faceRectDefault = DetectFaces(defaulCascade, image)
        eyes, eyesRect = DetectFaces(eyesCascade, image)
        # faces, faceRectAlt = DetectFaces(altCascade, image)
        # faces, faceRectAlt2 = DetectFaces(alt2Cascade, image)
        # faces, faceRectAltTree = DetectFaces(altTreeCascade, image)
 
        #Draw a rectangle around every found face
        for (x,y,w,h) in faceRectDefault:
            cv2.rectangle(image,(x,y),(x+w,y+h),(255,0,0),2)

        for (x,y,w,h) in eyesRect:
            cv2.rectangle(image,(x,y),(x+w,y+h),(0,0,255),2)

        cv2.putText(image, "Default: " + str(len(faceRectDefault)), (0,20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255,255,255), 1, cv2.LINE_AA)
        # cv2.putText(image, "Alt: " + str(len(faceRectAlt)), (0,40), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255,255,255), 1, cv2.LINE_AA)
        # cv2.putText(image, "Alt2: " + str(len(faceRectAlt2)), (0,60), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255,255,255), 1, cv2.LINE_AA)
        # cv2.putText(image, "Alt Tree: " + str(len(faceRectAltTree)), (0,80), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255,255,255), 1, cv2.LINE_AA)

        cv2.imshow("preview", image)

        key = cv2.waitKey(1)

        if key % 256 == 27:
            # ESC pressed
            print("Escape hit, closing...")
            break

    except Exception as ex:
        print(ex)
        break

cv2.destroyAllWindows()