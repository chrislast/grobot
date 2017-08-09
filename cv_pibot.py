#!/usr/bin/python
# import the necessary packages
# import numpy as np
import cv2
from picamera.array import PiRGBArray
from picamera import PiCamera
import time
import explorerhat as E
import logging as LOG

IDLE = 0
SCAN = 1
TRACK = 2
FOLLOW = 3

WIDTH = 320
HEIGHT = 240
FRAMES_PER_SECOND = 30

SCAN_TIMEOUT = 50   # ~2 seconds
MAX_TARGET_SIZE = 80    # target radius
MIN_TARGET_SIZE = 0.1   # target radius

class Servo(object):
    """servo motors used by pan tilt device"""
    def __init__(self, pin, min, max):
        if pin in (E.OUT1, E.OUT2, E.OUT3, E.OUT4):
            self.servo = E.Output(pin)
            self.min = min  # -90
            self.max = max  # +90
            self.frequency = 50  # Hz
            self.angle = 0
            self.point(self.angle)
            LOG.log(99, "Controlling a Servo motor on pin %d", pin)
        else:
            return None
    def point(self, degrees):
        """move the servo to a defined angle"""
        if degrees < -90:
            degrees = -90
        elif degrees > 90:
            degrees = 90
        self.angle = degrees
        mid = (self.min + self.max) / 2.0
        full = (self.max - self.min) / 2.0
        self.duty_cycle = full * degrees / 90.0 + mid
        self.servo.pwm(self.frequency, self.duty_cycle)

class Camera(object):
    """Camera and mount"""
    def __init__(self):
        """Create an object to capture video"""
        self.pan = Servo(E.OUT2, 88.61, 97.64)
        self.tilt = Servo(E.OUT1, 88.61, 96.39)
        LOG.log(99, "Created a Pan/Tilt Camera Mount")
        self.picam = PiCamera()
        LOG.log(99, "Camera started")
        self.picam.resolution = (WIDTH, HEIGHT)
        self.picam.framerate = FRAMES_PER_SECOND
        self.picam.rotation = 180
        # allow the camera to warmup
        time.sleep(0.1)
        LOG.log(99, "Camera ready")
    def look(self, pan, tilt):
        """point the camera in a specific direction"""
        self.pan.point(pan)
        self.tilt.point(tilt)
    def sleep(self):
        """turn the camera mount motors off temporarily"""
        self.pan.servo.off()
        self.tilt.servo.off()

class Driver(object):
    def __init__(self):
        """Create an object to control vehicle motion"""
        self.left_wheel = E.Motor(E.M2B, E.M2F)
        self.right_wheel = E.Motor(E.M1B, E.M1F)
        LOG.log(99, "Created a Robot Driver")
    def stop(self):
        """Stop both wheels"""
        self.left_wheel.stop()
        self.right_wheel.stop()
    def go(self, lspeed, rspeed):
        """Drive one or both wheels backwards or forwards"""
        if lspeed > 0:
            self.left_wheel.forwards(lspeed)
        else:
            self.left_wheel.backwards(-lspeed)
        if rspeed > 0:
            self.right_wheel.forwards(rspeed)
        else:
            self.right_wheel.backwards(-rspeed)

class Robot(object):
    def __init__(self):
        """Create a robot object"""
        self.camera = Camera()
        self.camera.look(0, 0)
        self.driver = Driver()
        self.driver.stop()
        self.state = IDLE
        self.scan_timeout = 0
        self.colours = {IDLE: E.light.blue,
                        SCAN: E.light.red,
                        TRACK: E.light.yellow,
                        FOLLOW: E.light.green}
        LOG.log(99, "Created a Robot")
    def change(self, state):
        """Change or confirm the current robot state"""
        if self.state != state:
            self.state = state
            E.light.off()
            self.colours[self.state].on()
    def track(self, targetsize, x, y):
        """Track and/or chase an object detected by CV"""
        self.change(TRACK)
        cpan = self.camera.pan.angle + (x - (WIDTH / 2)) / WIDTH * 20
        ctilt = robot.camera.tilt.angle + ((HEIGHT / 2) - y) / HEIGHT * 20
        self.camera.look(cpan, ctilt)
        if ctilt > 15:
            self.driver.stop()
        elif targetsize > MAX_TARGET_SIZE:
                self.driver.go(cpan, -cpan)
        else:
            if cpan > 0:
                self.driver.go(100, 100 - cpan)
            else:
                self.driver.go(100 + cpan, 100)
            self.change(FOLLOW)
        self.scan_timeout = 0
    def scan(self):
        """Look for an object by rotating camera and vehicle"""
        if self.scan_timeout > SCAN_TIMEOUT:
            self.idle()
            return
        self.change(SCAN)
        if self.camera.tilt.angle > 0:
            self.driver.go(100, -100)
        else:
            self.driver.go(-100, 100)
        self.scan_timeout += 1
    def idle(self):
        """Stop looking but keep watch in front"""
        if self.state != IDLE:
            self.change(IDLE)
            self.driver.stop()
            self.camera.look(0, 0)
            time.sleep(1)
            self.camera.sleep()

def cv_pibot(robot, display_windows=True):
    """function to command a robot"""
    # get a reference to the raw camera capture
    rawCapture = PiRGBArray(robot.camera.picam, size=(WIDTH, HEIGHT))
    # define the lower and upper boundaries of the "green"
    # ball in the HSV color space, then initialize the
    # list of tracked points
    greenLower = (0.11 * 256, 0.60 * 256, 0.20 * 256)
    greenUpper = (0.14 * 256, 1.00 * 256, 1.00 * 256)
    # initialise target lost counter
    lost_count = 0
    # capture frames from the camera
    for frame in robot.camera.picam.capture_continuous(rawCapture, format="bgr", use_video_port=True):
        # grab the raw NumPy array representing the image, then initialize the timestamp
        # and occupied/unoccupied text
        image = frame.array
        key = cv2.waitKey(1) & 0xFF
        # clear the stream in preparation for the next frame
        rawCapture.truncate(0)
        # if the `q` key was pressed, break from the loop
        if key == ord("q"):
            break
        # resize the frame, blur it, and convert it to the HSV
        # color space
        #image = imutils.resize(image, width=600)
        # blurred = cv2.GaussianBlur(frame, (11, 11), 0)
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        # construct a mask for the color "green", then perform
        # a series of dilations and erosions to remove any small
        # blobs left in the mask
        mask = cv2.inRange(hsv, greenLower, greenUpper)
        mask = cv2.erode(mask, None, iterations=2)
        mask = cv2.dilate(mask, None, iterations=2)
        # find contours in the mask and initialize the current
        # (x, y) center of the ball
        cnts = cv2.findContours(mask.copy(), cv2.RETR_EXTERNAL,
            cv2.CHAIN_APPROX_SIMPLE)[-2]
        center = None
        # only proceed if at least one contour was found
        if len(cnts) > 0:
            # find the largest contour in the mask, then use
            # it to compute the minimum enclosing circle and
            # centroid
            c = max(cnts, key=cv2.contourArea)
            ((x, y), radius) = cv2.minEnclosingCircle(c)
            M = cv2.moments(c)
            center = (int(M["m10"] / M["m00"]), int(M["m01"] / M["m00"]))
            # only proceed if the radius meets a minimum size
            if radius > MIN_TARGET_SIZE:
                lost_count = 0
                # draw the circle and centroid on the frame,
                # then update the list of tracked points
                cv2.circle(hsv, (int(x), int(y)), int(radius), (0, 255, 255), 2)
                cv2.circle(hsv, center, 5, (0, 0, 255), -1)
                cv2.putText(hsv, "x=%d, y=%d" % (x, y), (10, 50), cv2.FONT_HERSHEY_PLAIN, 1, (255, 255, 255), 2)
                cv2.putText(hsv, str(image[y, x].tolist()) + " - " + str(radius), (10,230), cv2.FONT_HERSHEY_PLAIN, 1, (255, 255, 255), 2)
                # Put Robot into target tracking mode
                robot.track(radius, x, y)
        else:
            # Put Robot into target scanning mode
            if lost_count > 4:
               robot.scan()
            else:
                lost_count += 1
        if display_windows:
            # show the frame to our screen
            cv2.imshow("Frame", hsv)

if __name__ == "__main__":
    try:
        # Create a robot instance and set it to work!
        robot = Robot()
        robot.idle()
        while not E.touch.four.is_pressed():
            pass
        cv_pibot(robot)
    finally:
        # cleanup the camera and close any open windows
        cv2.destroyAllWindows()
        robot.camera.picam.close()
