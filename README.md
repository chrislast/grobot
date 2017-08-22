# grobot
## Description
Ball chasing robot using OpenCV library on a Raspberry Pi.  Start it going and it will look for a tennis ball, track it with the pan/tiltable camera and chase it until it reaches it or it moves again.

![Grobot Picture](https://github.com/chrislast/grobot/blob/master/IMG_2046%5B1%5D.JPG)

## Parts List

| Component | Link | Cost |
| --- | --- | --- |
| Battery | [Anker PowerCore+ mini (3350mAh Premium Aluminum Portable Charger)](https://www.amazon.co.uk/gp/product/B005QI1A8C) | £9.99 |
| Camera Mount | https://shop.pimoroni.com/products/adafruit-mini-pan-tilt-kit-assembled-with-micro-servos | £19.50 |
| Motor driver board | https://shop.pimoroni.com/products/explorer-hat | £18 |
| Chassis + Wheels + motors | https://shop.pimoroni.com/products/sts-pi | £20 |
| Breadboard-plugins | https://shop.pimoroni.com/products/ecell-breadboard-plugin-connector | £1.20 |
| 30cm camera cable | https://shop.pimoroni.com/products/raspberry-pi-camera-cable | £3 |
| camera module | [Raspberry Pi v2.1 8 MP 1080p Camera Module (later version than mine)](https://www.amazon.co.uk/Raspberry-Pi-1080p-Camera-Module/dp/B01ER2SKFS) | £20.30 |
| OLED display | [1.3" OLED 128x64 monochrome SPI display](https://www.amazon.co.uk/gp/product/B01GC6C1CA) | £8.99 |
|	| Total | £100.98 |

and some linker cables and a micro usb cable, oh and a raspberry pi!

I got most of that cheaper with discount codes or already had it, but that’s the full price list today

## Python Source Code
https://github.com/chrislast/grobot/blob/master/cv_pibot.py

## Features
	[X] Identify coloured object
	[X] Camera tracking with pan/tilt mount
	[X] Object Chasing
	[X] Scan when lost
	[X] Sleep mode
	[X] HSV desktop display window with target info overlay
	[X] Mode indication lighting
	[X] Proximity-based watch and wait
	[X] Aerial tracking
	[X] Start on boot - Spawn (15s delayed start) from /etc/rc.local
	[X] Capacitive touch start button
	[X] On board HTTP Server for CV display
	[X] Improve scan mode, look first swivel later!

## Future Enhancements
	[ ] Distance Sensor instead of target radius for more reliable stop detection
	[ ] Predictive Target tracking
	[ ] Accelerometer/Compass Position tracking and recording
	[ ] Sound
	[ ] Improved object detection
		[X] Added Blur stage
		[ ] Use Shape detection
	[ ] 132x64 OLED Display
		[X] Webserver IP address
		[ ] Target Range
		[X] FPS Info
		[X] Realtime CV thumbnail
	[ ] Direct drive control mode

## Performance optimisations
	[ ] Performance mode option removing webserver/thumbnail
	[ ] Boot to command line not desktop
	[ ] Direct write to OLED bit array to replace 128x64xdraw_pixel()
	[ ] CV step cost/benefit analysis
	[ ] CPU usage profiling
	[ ] GPU usage profiling
