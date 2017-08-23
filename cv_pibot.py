#!/usr/bin/python
# import the necessary packages
# import numpy as np
import cv2
from picamera.array import PiRGBArray
from picamera import PiCamera
import time
import explorerhat as E
import logging as LOG
import numpy as N
import socket
import random
import gaugette.sh1106
import gaugette.gpio
import gaugette.spi

IDLE = 0
SCAN = 1
TRACK = 2
FOLLOW = 3
MANUAL = 4

WIDTH = 320
HEIGHT = 240
FRAMES_PER_SECOND = 30

SCAN_TIMEOUT = FRAMES_PER_SECOND * 6 / 2   # ~6 seconds
SCAN_STEPS = 32 # camera rotation points during scan start 
MAX_TARGET_SIZE = 80    # target radius
MIN_TARGET_SIZE = 0.1   # target radius

# SPI DISPLAY
DC_PIN = 16     # DATA/COMMAND on GPIO 15
RESET_PIN = 15  # GPIO 14
# OTHER GPIOS USED - SCLK 11, MOSI 10, CHIP SELECT 8

class Oled(object):
    """SSD1306 OLED device"""
    def __init__(self):
        _gpio = gaugette.gpio.GPIO()
        _spi = gaugette.spi.SPI(0,0)
        _oled = gaugette.sh1106.SH1106(_gpio, _spi, dc_pin=DC_PIN, reset_pin=RESET_PIN)
        _oled.begin()
        _oled.clear_display()
        _oled.draw_text2(2, 0, "Grobot v0.2", size=1)
        _oled.display()
        _oled.fps_time = time.time()
        _oled.bmp = gaugette.sh1106.SH1106.Bitmap(132,64)
        self.oled = _oled
        LOG.log(99, "Started OLED display")

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
        self.scan_timeout = -SCAN_STEPS
        self.colours = {IDLE: E.light.blue,
                        SCAN: E.light.red,
                        TRACK: E.light.yellow,
                        FOLLOW: E.light.green,
                        MANUAL: E.light.all}
        _oled = Oled()
        self.oled = _oled.oled
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
                self.driver.go(100, 100 - 2 * cpan)
                LOG.log(99, "Target right %d %d", 100, 100 - 2 * cpan)
            else:
                self.driver.go(100 + 2 * cpan, 100)
                LOG.log(99, "Target left %d %d", 100 + 2 * cpan, 100)
            self.change(FOLLOW)
        self.scan_timeout = -SCAN_STEPS
    def scan(self):
        """Look for an object by rotating camera and vehicle"""
        if self.scan_timeout > SCAN_TIMEOUT:
            self.idle()
            return
        self.change(SCAN)
        if self.scan_timeout == -SCAN_STEPS:
            # create a search pattern coordinate list
            p = self.camera.pan.angle
            t = self.camera.tilt.angle
            self.scan_pattern = [(p+int(45*N.sign(p+0.1)*N.cos(N.radians(n))),
                                  t+int(30*N.sign(t+0.1)*N.sin(N.radians(n))))
                                 for n in range(0,360,360/SCAN_STEPS)]
        if self.scan_timeout < 0:
            # Look at the next search location
            pan, tilt = self.scan_pattern[self.scan_timeout]
            self.camera.look(pan, tilt)
        else:
            # Reset the camera to staight ahead
            self.camera.look(0, 0)
            if self.scan_pattern[-SCAN_STEPS][0] > 0:
                # Rotate left
                self.driver.go(100, -100)
            else:
                # Rotate right
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
    def manual(self):
        """@@TODO - Add manual remote drive method"""
        pass

def cv_pibot(robot):
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
        # image = imutils.resize(image, width=600)
        blurred = cv2.GaussianBlur(image, (11, 11), 0)
        hsv = cv2.cvtColor(blurred, cv2.COLOR_BGR2HSV)
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
        if cnts:
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
                cv2.putText(hsv, "x=%d, y=%d" % (x, y), (10, 50),
                            cv2.FONT_HERSHEY_PLAIN, 1, (255, 255, 255), 2)
                cv2.putText(hsv, str(image[y, x].tolist()) + " - " + str(radius),
                            (10, 230), cv2.FONT_HERSHEY_PLAIN, 1, (255, 255, 255), 2)
                # Put Robot into target tracking mode
                robot.track(radius, x, y)
            else:
		cv2.putText(hsv, "radius=%d" % radius, (10, 50),
                            cv2.FONT_HERSHEY_PLAIN, 1, (255, 255, 255), 2)
        else:
            cv2.putText(hsv, "Target Lost", (10, 50),
                       cv2.FONT_HERSHEY_PLAIN, 1, (255, 255, 255), 2)
            # Put Robot into target scanning mode
            if lost_count > 4:
                robot.scan()
            else:
                lost_count += 1
        # show the frame to our screen
        status=cv2.imwrite("/home/pi/Desktop/grobot/html/img.png", hsv)
        new_time = time.time()
        # update the OLED display
        grayimage = cv2.cvtColor(image,cv2.COLOR_BGR2GRAY)
        smallgrayimage = cv2.resize(grayimage, (128, 64))
        # convert to 1 bit monochrome values with dynamic threshold
        _, bwimage = cv2.threshold(smallgrayimage, 128, 1, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
	# convert to a list so we can reverse the rows because bitmaps
        # like to start from the bottom row
        _data = bwimage.tolist()
        _data.reverse()
        # flatten the list
        _bits = [row for rows in _data for row in rows]
        # Convert the list of bits to a list of bytes in the oled bitmap array
	robot.oled.bmp.data=[]
        while _bits:
            # Accumulate 8 bits into a byte
            acc = 0
            for bit in _bits[:8]:
                acc <<= 1
                acc += bit
            robot.oled.bmp.data.append(acc)
            bits = bits[8:]
	robot.oled.bmp.display_block(0, 0, 0, 0)
        fps = 1 / (new_time - robot.oled.fps_time)
        robot.oled.fps_time = new_time
        robot.oled.draw_text(2, 1, "FPS %.1f " % fps)
        robot.oled.display()

if __name__ == "__main__":
    try:
        # Create a robot instance and put it into idle mode
        robot = Robot()
        robot.idle()
        robot.camera.sleep()
        # Get the IP address of this pi so it can be used to see the webserver
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))  # google DNS
        global IP_ADDRESS
        IP_ADDRESS = s.getsockname()[0]
        s.close()
        robot.oled.draw_text(2, 9, "IP Address %s" % IP_ADDRESS)
        robot.oled.display()
        # Wait for cap touch button four to be pressed
        while not E.touch.four.is_pressed():
            pass
        del E.touch
        # start the FPS timer
        robot.oled.fps_time = time.time()
        # Set the robot to work
        cv_pibot(robot)
    finally:
        # cleanup the camera and close any open windows
        cv2.destroyAllWindows()
        robot.camera.picam.close()
