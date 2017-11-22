"""ewrwe."""
# import the necessary packages
import imutils
import cv2

# define the lower and upper boundaries of the "green"
# ball in the HSV color space, then initialize the
# list of tracked points


smarties = {
    "red": {
        "lower": (175, 100, 28),
        "upper": (182, 204, 203),
        "bgr": (0, 0, 255)},
    "orange": {
        "lower": (7, 115, 108),
        "upper": (12, 212, 255),
        "bgr": (0, 165, 255)},
    "yellow": {
        "lower": (20, 100, 100),
        "upper": (31, 204, 203),
        "bgr": (0, 255, 255)},
    "green": {
        "lower": (31, 52, 28),
        "upper": (52, 204, 203),
        "bgr": (0, 255, 0)},
    "blue": {
        "lower": (98, 22, 28),
        "upper": (113, 204, 203),
        "bgr": (255, 0, 0)},
    "pink": {
        "lower": (149, 40, 40),
        "upper": (174, 200, 200),
        "bgr": (128, 128, 255)},
    "violet": {
        "lower": (114, 22, 0),
        "upper": (164, 77, 166),
        "bgr": (255, 0, 255)},
    "brown": {
        "lower": (5, 71, 44),
        "upper": (21, 157, 137),
        "bgr": (0, 100, 100)},
}

for pic in (('IMG_2349.JPG',)):
    bgr = cv2.imread(pic)
    # resize the frame, and convert it to the HSV color space
    bgr = imutils.resize(bgr, width=600)
    hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)

    offset_y = 0
    total = 0
    for smartie in smarties:
        # Perform a series of dilations and erosions to remove any small
        # blobs left in the mask
        image = cv2.inRange(hsv, smarties[smartie]["lower"], smarties[smartie]["upper"])
        image = cv2.erode(image, None, iterations=2)
        image = cv2.dilate(image, None, iterations=2)

        # find contours in the mask and initialize the current
        # (x, y) center of the ball
        smarties[smartie]["cnts"] = cv2.findContours(image.copy(), cv2.RETR_EXTERNAL,
                                                     cv2.CHAIN_APPROX_SIMPLE)[-2]
        center = None

        # only proceed if at least one contour was found
        if len(smarties[smartie]["cnts"]) > 0:
            subtotal = 0
            for c in smarties[smartie]["cnts"]:
                ((x, y), radius) = cv2.minEnclosingCircle(c)
                M = cv2.moments(c)
                center = (int(M["m10"] / M["m00"]), int(M["m01"] / M["m00"]))
                # only proceed if the radius meets a minimum size
                # print radius  # included for debug
                if radius > 8:
                    # draw the circle on the original picture
                    cv2.circle(bgr, (int(x), int(y)), int(radius),
                               smarties[smartie]["bgr"], 2)
                    subtotal += 1
            cv2.putText(bgr,
                        "%d %ss" % (subtotal, smartie),
                        (10, 25 + offset_y),
                        cv2.FONT_HERSHEY_PLAIN,
                        1.5,
                        smarties[smartie]["bgr"], 2)
            offset_y += 24
            total += subtotal

    cv2.putText(bgr,
                "%d smarties" % total,
                (10, 25 + offset_y),
                cv2.FONT_HERSHEY_PLAIN,
                1.5,
                (0, 0, 0), 2)
    # show the frame to our screen
    cv2.imshow(pic, bgr)

# Wait here until key pressed in an open CV window
cv2.waitKey(0)

# close any open window
cv2.destroyAllWindows()
