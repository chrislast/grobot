import cv2
import numpy as np

colors = []
camera = PiCamera()
camera.resolution = (320, 240)
camera.framerate = 32
camera.rotation = 180
#camera.awb_mode = camera.AWB_MODES['off']
#camera.exposure_mode = camera.EXPOSURE_MODES['off']
rawCapture = PiRGBArray(camera, size=(320, 240))

# allow the camera to warmup
time.sleep(0.1)

def on_mouse_click (event, x, y, flags, frame):
    if event == cv2.EVENT_LBUTTONUP:
        colors.append(frame[y,x].tolist())

for frame in camera.capture_continuous(rawCapture, format="bgr", use_video_port=True):
    # grab the raw NumPy array representing the image, then initialize the timestamp
    # and occupied/unoccupied text
    image = frame.array
    key = cv2.waitKey(1) & 0xFF
    if key == ord('q'):
        break
    # clear the stream in preparation for the next frame
    rawCapture.truncate(0)
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    if colors:
        cv2.putText(hsv, str(colors[-1]), (10, 50), cv2.FONT_HERSHEY_PLAIN, 2, (0, 0, 0), 2)
    cv2.imshow('frame', hsv)
    cv2.setMouseCallback('frame', on_mouse_click, hsv)

cv2.destroyAllWindows()

    # avgb = int(sum(c[0] for c in colors) / len(colors))
    # avgg = int(sum(c[0] for c in colors) / len(colors))
    # avgr = int(sum(c[0] for c in colors) / len(colors))
    # print avgb, avgg, avgr

minb = min(c[0] for c in colors)
ming = min(c[1] for c in colors)
minr = min(c[2] for c in colors)
maxb = max(c[0] for c in colors)
maxg = max(c[1] for c in colors)
maxr = max(c[2] for c in colors)
print minr, ming, minb, maxr, maxg, maxb

lb = [minb,ming,minr]
ub = [maxb,maxg,maxr]
print lb, ub
