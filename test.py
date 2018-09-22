import imp

try:
    imp.find_module('picamera')
    imp.find_module('picamera.array')
    from picamera.array import PiRGBArray
    from picamera import PiCamera
except ImportError:
    found = False

print(found)