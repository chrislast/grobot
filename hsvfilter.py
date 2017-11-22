"""
Tool to help create a HSV mask from an image.

Q to quit
w,s,e,d,r,t adjust lower hsv bound
i,j,o,k,p,l adjust upper hsv bound
"""
import cv2
import imutils

colors = []

image = cv2.imread('IMG_2349.JPG')
image = imutils.resize(image, width=600)
hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
cv2.imshow("Frame", image)

lh = ls = lv = 0
hh = hs = hv = 255

while True:
    mask = cv2.inRange(hsv, (lh, ls, lv), (hh, hs, hv))
    cv2.putText(mask,
                "[%d, %d, %d], [%d, %d, %d]" % (lh, ls, lv, hh, hs, hv),
                (10, 50),
                cv2.FONT_HERSHEY_PLAIN,
                2,
                (128, 128, 128),
                2)
    cv2.imshow("Mask", mask)
    key = cv2.waitKey(0)
    if key == ord('q'):
        break
    elif key == ord('w') and lh < 255:
        lh += 1
    elif key == ord('s') and lh:
        lh -= 1
    elif key == ord('e') and ls < 255:
        ls += 1
    elif key == ord('d') and ls:
        ls -= 1
    elif key == ord('r') and lv < 255:
        lv += 1
    elif key == ord('f') and lv:
        lv -= 1
    elif key == ord('i') and hh < 255:
        hh += 1
    elif key == ord('j') and hh:
        hh -= 1
    elif key == ord('o') and hs < 255:
        hs += 1
    elif key == ord('k') and hs:
        hs -= 1
    elif key == ord('p') and hv < 255:
        hv += 1
    elif key == ord('l') and hv:
        hv -= 1
    elif key == ord(' '):
        lh = ls = lv = 0
        hh = hs = hv = 255

cv2.destroyAllWindows()
