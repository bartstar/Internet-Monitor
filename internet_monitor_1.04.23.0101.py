##
###
# Speed testing program to measure internet download, upload, and ping
# Inspired by and loosly based on Instructables.com version 0.4 by HoChri (aka Legufix)
# Setup for LED touch screen, resolution 1280 x 768
#
# Version v-1.04.23.0101 Current version corrects error in storing database values at midnight
# This is written in Python 3
# Version 1 is production version
# By BartStar
#
# Database (internet_mon.db) is linear text data with each line a datapoint. Database is needed to hold configuration parameters and
# history of speedtests. Data stored is as follows, each representing a line in the textual database. Since data is in text format
# conversions take place during read and write functions.
#  0 - Defines parameters in row 1
#  1 - day of month (1-31) of last stored speedtest
#  2 - Defines parameters in next 30 rows
#  3-32 - last 30 days of speedtest upload results in MBpss - this is average of all upload tests each day
#  33 - Defines parameters in next 30 rows
#  34-63 - last 30 days of speedtest download speeds in MBps - this is average of all download tests each day
#  64 - Defines parameters in next 48 rows
#  65-113 - last 24 hours of speedtest download speeds (every 30 min) - 48 data points
#  114 - Defines parameters in next 48 rows
#  115-161 - last 24 hours of speedtest upload speeds (every 30 min) - 48 data points
#  162 - Defines parameters in last rows
#  163 - last database index
#  164 - 174 - configuration parameters
#        164 - router reboot time (seconds) default is 180
#        165 - modem reboot time (seconds) default is 120
#        166 - relays (to cycle power for modem and router) enabled (True / False)
#        167 - Ubidots upload enabled (True / False)
#        168 - Max download speed for meter display (in MBps) default is 500
#        169 - Max upload speed for meter display (in MBps) default is 50
#        170 - Max ping time for meter display (in Sec) default is 50
#        171 - Speedtest retry number of times before failing - default is 3
#        172 - Speedtest lower limit for failure - default is 4 (4 MBps)
#        173 - Simple ping test - time between tests - default is 60 sec
#        174 - Logging True or False (default is True)
#
# Some parameters can be changed in System Options Menu, such as:
#   Relays to cycle power to modem and router - relays_enabled (default is True)
#   Option to send data to Ubidots - ubidots_enabled (default is False)
#   Router boot time - routerdelay
#   Modem boot time - modemdelay
#   Meter in main display, max values
#     Download max speed - maxdlmeter (in MBps - default is 500)
#     Upload max speed - maxulmeter (in MBps - default is 50)
#     Ping max time - maxpingmeter  (in seconds - default is 50)
#   Speedtest parameters
#     Max number of iterations speedtest will try before failing - maxiterations (default is 3)
#     Lower limit (threshold) of speedtest download speed - if under this value, speedtest is failure - lower_limit (default is 4 MBps)
#   Time between ping tests (default is 30 seconds)
#
# Other parameters must be changed in code:
#    Ubidots TOKEN and Device Label for uploads
#    Number of attempts to upload Ubidots data (will attempt 5 times before failure)
#    Time between speedtests (default is 30 minutes)
#    Logging level for bw.log (default is 'Warning' level. Some additional logging data is available at 'Info' level, but this must be changed in code)
#    Debugging log messages are available by setting log level to 'Debug'
#
# Operation notes:
#  A log file is written to a  file in /home/pi. The log file name is changed daily as "imon-ddmm.log" where dd is the day of the month and mm is the
#    month of the year as a number (01-12). If the program is restarted more than once in a day, new log entries will be appended to the current log file.
#    It is recommended that log files be deleted at least monthly using the "rm bw-ddmm.log" command at terminal to clear storage space.
#    Logging can be turned completely off in the configuration menu. Logfile will always be created at startup, but logging can be turned off after
#  At startup, screen will remain blank until initial speedtest is completed
#  Speedtest will usually be conducted every 30 minutes. The connection is an https: (secure) connection.
#    If Speedtest encounters an HTTP 403 error (the speedtest server is refusing to answer) or a can't connect to the server error,
#    the speedtest will be repeated every 60 seconds until successful or another error is encountered.  If there are three general failures,
#    the system will try a ping test to the Google DNS Server just to verify an internet outage.
#    If the ping is successful, a zero response is recorded from the speedtest server and the program will continue normal operations.
#  Ping tests with the Google DNS server will take place every 60 seconds between normal speedtests - three failuress in a row  will trigger a speedtest
#  LED will be illuminated BLUE during speedtests
#  LED will be illuminated RED if speedtest fails until program attempts retry
#  Averages of download speeds and upload speeds exclude data entries that are zero - such as when server is undergoing maintenanct or other server issues
#  Time to next speedtest is approximate (not exact)
#  Ops Cycle shows the count of speedtests attempted
#  Program will reboot at 00:07 (7 minutes after midnight to clear system memory, ops cycle will start over at 1 (reboot is setup in raspian, not in program)
#  Booted will show time of last program start
#  24-Hr barchart (left side of screen) shows speedtests over the last 24 hours. Orange bar is the latest
#  Month barchart (right side of screen) shows ping times (Orange) and download speeds (Blue). Most recent are left Orange and Blue bars
#  Speedtest can be manually initiated by pressing blue button on left side of screen
#  System Options Menu can be called by pressing blue button at top right of screen
#  To kill the program, go into System Options Menu and select red "kill" button at bottom left of window of
#    do an ALT-TAB from keyboard attached to the Raspberry Pi, which will bring a command window to the screen. Click the "x" in the upper right corner to kill it.
#  Because threading is used in this code, the system will become unstable after operating several days, so an automatic reboot is required
#    To set up the reboot, at terminal window, enter sudo crontab -e, then enter the following line as the last line - this will reboot the Pi at 0:07am (7 minutes after midnight) each morning
#        07 00 * * * /sbin/shutdown -r now
#    Save the crontab and exit 
#    An entry in Autostart is also required to automatically start the program with root privaleges after reboot. The ping function requires
#    root (administrator) privaleges. In a terminal window, enter
#        sudo nano /etc/xdg/lxsession/LXDE-pi/autostart
#    Enter the following line in the file as the last lin:
#        @sudo lxterminal -e /usr/bin/python3 /home/pi/internet_monitor_prod.py
#    Delete or rename autostart file at .config/lxsession/LXDE-pi, otherwise the autostart file at /etc/xdg ... will not run (the one at .config ...) doesn't have
#    root privaleges. The Bandwidth Monitor program will fail if run from this location. 
# ******************************************************************************/
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documnetation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to  whom the Software is
# furished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS OR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
###
from tkinter import *
from tkinter import font
import time
import monotonic; mtime = monotonic.time.time  # Mtime() is monotomic time in fractional seconds
import math, numpy
import threading  #For process threading
import requests
import speedtest
import RPi.GPIO as GPIO
import numpy as np
import matplotlib
import tkinter as tk
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
import datetime
from datetime import date
from datetime import timedelta
import logging
import sys
import traceback
from pythonping import ping

# Define startup variables and set conditions
version = "v-1.02.1010.22"
author = 'by Bart'
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
RELAY_1 = 21  # GPIO pin number for Modem relay
RELAY_2 = 22  # GPIO pin number for Router relay
GPIO.setup(RELAY_1, GPIO.OUT)
GPIO.output(RELAY_1, GPIO.HIGH)
GPIO.setup(RELAY_2, GPIO.OUT)
GPIO.output(RELAY_2, GPIO.HIGH)

loggingfile=True
internet_down = False
internet_outage_reported = False
speedtest_conducted=False
speedtest_ready=True # Flag to indicate everything is ready for speedtest
current_time = time.strftime("%H:%M:%S, %d.%m.%Y")
# Create or open log file
day=time.strftime("%d")
month=time.strftime("%m")
logfilename = "/home/pi/imon-"+str(month)+str(day)+".log"
# Set up logging to bw.log file (levels are DEBUG, INFO, and WARNING)
# DEBUG provides logging reports of various types oriented towards finding program errors, in addition to INFO and WARNINGS
# INFO will record in the log the same data that is shown on the display, but in programming sequence, in addition to WARNINGs
# WARNING will display errors that occur in Speed tests or Ping tests 
# Most log entries will carry the name or abbreviation of the code function where they are written from
# Change code below for level of logging desired
logging.basicConfig(filename=logfilename, filemode='a', level=logging.WARNING,format='%(asctime)s %(message)s')

# Arrays for daily bandwidth upload values and bandwidth download speed (30 days)
# The following numbers are placeholders to define the matrix and will be replaced over the first 30 days
bwu = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
             0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
bwd = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
             0, 0, 0, 0, 0, 0, 0, 0, 0, 0]

# bwdevents holds the last 24 hours (48 data points) of download speed tests
# The following numbers are placeholders to define the matrix and will be replaced over the first 24 hours
bwdevents = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18,
             19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34,
             35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48]
bwuevents = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18,
             19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34,
             35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48]
adl24 = 0 #Average of last 24 hours download speeds
adu24 = 0 #Average of last 24 hours upload speeds
ip_list = '8.8.8.8' # Internet IP address for Google DNS Server for ping checks
goodping = True  # Boolean value is True if ping to Google DNS Server is good, False if not
speedtest_start=True
countdown_thread_name="Thread-00:00"
bdown = 0.0 # Temporary holder of download speed
bup = 0.0   # Temporary holder of upload speed
bw_down = 0.0  # Holds speedtest for download speed
bw_up = 0.0    # Holds speedtest for upload speed
download_speed = 0.0
upload_speed = 0.0
ping_time = 0.0 # Holds speedtest for ping time to speedtest server
timedelay = 1800 # Time in between speedtests (30 min)
t0 = 0.0         # Used in update_clock function
last_dbindex = 0 # Array pointer of last speedtest entry
last_tested = time.localtime()
opscounter = 0  # Counter of times speedtest is run without failure
net_status = True  # True if speedtest successful, False if failed
test = 0
GREEN = 5  # GPIO Pin number for green LED connection
BLUE = 6  # GPIO Pin number for blue LED connection
RED = 13  # GPIO Pin number for red LED connection

# Meter limits (see Options menu to change)
maxdlmeter = 500  # Max setting for round download speed meter
maxulmeter = 50  # Max setting for round upload speed meter
maxpingmeter = 50  # Max setting for round ping response time meter

# Setup menu variables (see Options menu to change)
relays_enabled = True
ubidots_enabled = False
routerdelay = 180
modemdelay = 120
pingtestdelay = 60 # Time in seconds between ping tests

# Setup General Purpose Input/Output (GPIO) pins on Raspberry Pi
GPIO.setup(GREEN, GPIO.OUT)
GPIO.setup(BLUE, GPIO.OUT)
GPIO.setup(RED, GPIO.OUT)
GPIO.output(GREEN, GPIO.LOW)  #Set initial output to LOW - meaning zero volts)
GPIO.output(BLUE, GPIO.LOW)
GPIO.output(RED, GPIO.LOW)

# Setup Ubidots information
post = False #True if successful upload to Ubidots, False if unsuccessful upload
TOKEN = "BBFF-GFPFhG0XXeL1I8IBJPRFL59ZtX1kZR"  # Token for Ubidots access
DEVICE_LABEL = "raspberry-bandwidth-monitor"  # Put your device label here
VARIABLE_LABEL_1 = "Upload"  # Put your first variable label here
VARIABLE_LABEL_2 = "Download"  # Put your second variable label here
VARIABLE_LABEL_3 = "Ping"  # Put your third variable label here

# Download speedtest threshold settings (see Options menu to change)
lower_limit = 4  # Threshold (4 MBps)  for download speed -> router &  modem will be reset
max_iterations = 3

# Database definitions
database="/home/pi/internet_mon.db"
database_def=["Row0-internet_mon.db, Row 1 is day of month last stored",
              "Row2-Rows 3-32 are last 30 days of upload speed results",
              "Row33-Rows 34-63 are last 30 days of download speed results",
              "Row64-Rows 65-113 are last 24 hours of download speed results",
              "Row114-Rows 115-161 are last 24 hours of upload speed results",
              "Row162-Rows 163-174 are configuration parameters"]

# Get today's date & time
today = date.today()
timestart = time.localtime()

# Log startup
logging.warning('#########################')
logging.warning('Internet Monitor started')

def quit(*args):  # Function to exit this program. In monitor, press ctrl-z to stop Python
    root.destroy()
    sys.exit('Program stopped via touch screen button or ESCAPE button')
    ##End of function quit##

def update_clock():  # Function to update clock during sleep periods
    global timedelay
    global speedtest_ready
    global t0 # t0 is set to mtime in update_speedtest
    now = time.localtime()
    txt = time.strftime("%H:%M:%S", now)
    lbl2.config(text=txt)
    finish = t0 + timedelay
    timeto = int(finish - mtime())
    elapsed = int(mtime() - t0)
    mins, secs = divmod(timeto, 60)
    timer = '{:02d}:{:02d}'.format(mins, secs)
    lbl21.config(text=timer)
    root.after(10, lambda:update_clock())  # reschedule update_clock function every 1000ms
    ##End of function update_clock##

def start_speedtest():  # Function called when manual speedtest button is pushed
    global speedtest_ready
    speedtest_ready = True
    logging.warning('Manual speedtest selected')
    update_speedtest()

def update_speedtest():  # Overall speedtest function, includes sub functions to display results
    global current_time
    global ping_time
    global last_tested
    global bw_down
    global bw_up
    global adl24
    global adu24
    global bdown
    global test
    global goodping
    global opscounter
    global timestart
    global last_tested
    global post
    global pingtestdelay
    global speedtest_ready
    global speedtest_conducted
    global internet_down
    global internet_outage_reported
    global lower_limit
    global speedtest_start
    global countdown_thread_name
    global loggingfile

    # Update_speedtest Functions

    # Color LED functions are used to turn the LED on (state is True) or turn it off (state is False)
    def LED_onoff(color, state):
        if color == "green":
            green_LED_on(state)
            blue_LED_on(False)
            red_LED_on(False)
        if color == "red":
            red_LED_on(state)
            blue_LED_on(False)
            green_LED_on(False)
        if color == "blue":
            blue_LED_on(state)
            red_LED_on(False)
            green_LED_on(False)
        ##End of function LED_onoff##

    def green_LED_on(state):
        if state:
            GPIO.output(GREEN, GPIO.HIGH)
        else:
            GPIO.output(GREEN, GPIO.LOW)
        ##End of function green_LED_on##

    def blue_LED_on(state):
        if state:
            GPIO.output(BLUE, GPIO.HIGH)
        else:
            GPIO.output(BLUE, GPIO.LOW)
        ##End of function blue_LED_on##

    def red_LED_on(state):
        if state:
            GPIO.output(RED, GPIO.HIGH)
        else:
            GPIO.output(RED, GPIO.LOW)
        ##End of function red_LED_on##

    def speed():  # Function to conduct speedtest, output data is bw_down, bw_up, ping_time & post
        global net_status
        global lower_limit
        global opscounter
        global routerdelay
        global modemdelay
        global ubidots_enabled
        global relays_enabled
        global bw_down
        global bw_up
        global ping_time
        global post
        global pingtestdelay
        global goodping
        global t0
        global speedtest_conducted
        global internet_down
        global internet_outage_reported
        global lower_limit
        global loggingfile

        # Speed functions
        def post_request(payload):  # Ubidots upload function
            # Payload comes from Speed Function
            # Post_Request Function - Creates the headers for the HTTP requests to Ubidots
            url = "http://things.ubidots.com"
            url = "{}/api/v1.6/devices/{}".format(url, DEVICE_LABEL)
            headers = {"X-Auth-Token": TOKEN, "Content-Type": "application/json"}
            # Makes the HTTP requests
            status = 400
            attempts = 0
            while status >= 400 and attempts <= 5:
                try:
                    req = requests.post(url=url, headers=headers, json=payload)
                    status = req.status_code
                    attempts += 1
                    time.sleep(1)
                except:
                    attempts += 1
                    time.sleep(1)
            # Processes results
            if status >= 400:
                if loggingfile:
                    logging.warning('>>>>>> Post-Request - Could not send Ubidots data after 5 attempts, please check your token credentials and internet connection')
                return False
            if loggingfile: logging.info('Post-Request - Ubidots updated. Status = %s', status)
            return True # True is returned if upload is successful
            ##End of function post_request##

        def waitandblink(t):  #Function to blink LED with rotating red, green, blue flashes for "t" amount of time
            # Operates a loop of LED's on for 1/2 second each, for an approximate loop period of 1.5 seconds
            loops = int(t/1.5) #If t=30 seconds, twenty loops will be run
            for i in range(1,loops,1):
                LED_onoff("blue",True)
                time.sleep(0.5)
                LED_onoff("red",True)
                time.sleep(0.5)
                LED_onoff("green",True)
                time.sleep(0.5)
                green_LED_on(False)
            ##End of function waitandblink##

        i = 0
        do_ubidots=True
        retry=0
        bw_down = 0.0 #Must start with zero download speed for logic
        speedtest_conducted = False
        currentDateAndTime = datetime.datetime.now()
        post = False #Starting boolean value returned when posting results to Ubidots
        while bw_down < lower_limit:
            i += 1
            if i <= max_iterations:
                if loggingfile: logging.debug('Speed-Speedtest Iteration %d', i)
            if i > max_iterations:
                ping_test()  # Try a ping test with the Google DNS server. If this is successful, Intenet is still functioning
                if goodping: # Error is possibly a problem with the speedtest server instead
                    net_status = True
                    internet_down=False
                    LED_onoff("blue", False)
                else:
                    if relays_enabled:
                        GPIO.output(RELAY_1,GPIO.LOW) # Kill power to modem
                        if loggingfile: logging.warning('>>>>>> Speed-Speedtest failed - exceeded max iterations - Modem power reset')
                        waitandblink(5) # Sleep 5 seconds before restoring power to modem
                        GPIO.output(RELAY_1,GPIO.HIGH) # Restore power
                        if loggingfile: logging.warning('>>>>>> Speed-Modem power restored')
                        lbl7.config(text="Speed-Speedtest failed. Modem/Router reset", bootstyle=WARNING)
                        waitandblink(modemdelay) # Give 'modemdelay' seconds for modem to reset before resetting router
                        GPIO.output(RELAY_2,GPIO.LOW) #Kill power to router
                        if loggingfile: logging.warning('>>>>>> Speed-Router power interrupted for reset \n')
                        waitandblink(10) # Sleep 10 seconds before restoring power to router
                        GPIO.output(RELAY_2,GPIO.HIGH) #Restore power to router
                        waitandblink(routerdelay) #Sleep 'routerdelay' seconds while router reboots
                        lbl7.config(text="Modem/Router reset, trying speedtest again", bootstyle=SUCCESS)
                    net_status = False
                    LED_onoff("red", True)
                    internet_down=True
                bw_down = 0.0
                bw_up = 0.0
                ping_time = 0.0
                speedtest_conducted=True
                break # End the While loop

            try:
                LED_onoff("blue", True)  ## Turn on Blue LED to show speed test underway
                st = speedtest.Speedtest(secure=True) # Conduct speedtest
                st.get_best_server()  # Contact speedtest server closest to me
                bw_down = round(st.download(threads=None)/1E6, 2) # Get download speed result, reduce to MBps
                bw_up = round(st.upload(pre_allocate=True, threads=None)/1E6, 2) # Get upload speed result, pre-allocation builds packets before sending, reduce to MBps
                results_dict = st.results.dict()  # Get ping result
                ping_time = round((results_dict['ping']), 2) # extract ping result number
                net_status = True #Assume network is working
                LED_onoff("blue",False) # Turn off Blue LED
                if retry > 0:
                    if loggingfile: logging.warning('>>>>>> Speed-Speedtest completed successfully, returning to normal operation. \n')
                if loggingfile: logging.info('Speed-Speedtest complete. BW Down = %s, BW up = %s , Ping = %s', bw_down, bw_up, ping_time)
                speedtest_conducted=True
                do_ubidots=True
                internet_down=False

            except Exception as e:  # This section executes upon an error encountered in the try section
                e = traceback.format_exc()
                if loggingfile: logging.warning('>>>>>> Speed-Exception error in speedtest, iteration %d. Traceback error = %s \n',i,e)
                LED_onoff("blue",False) # Turn off Blue LED
                # Check to see if error is HTTP Error 403. If so, speedtest server is alive, but not handling the request. Keep trying.
                if ("HTTP Error 403" in e) or ("Unable to connect to servers" in e):
                    net_status = True # Error 403 is server refusing to answer, try again
                    LED_onoff("red",False)
                    speedtest_conducted=True
                    internet_down=False
                    i -= 1 # Log the problem and decrement the test count
                    retry = retry + 1
                    if loggingfile: logging.warning('>>>>>> Speed-Speedtest not responding - trying again in 1 min. Retry=%d, OpsCycle=%d \n', retry, opscounter)
                    do_ubidots=False
                else:
                    LED_onoff("red",True) # Turn on, Red LED to indicate errors are symptoms of internet failure
                    bw_down = 0.0
                    bw_up = 0.0
                    ping_time = 0.0
                    do_ubidots=True
                    net_status = False #Assume network is down, mark speedtest as failed
                    speedtest_conducted=True
                    internet_down=True
                    if loggingfile: logging.debug('Speed-Speedtest below lower_limit, attempting to try again in 60 sec. Download = %s , Net_status = TRUE ', bw_down)
                    if opscounter == 0:
                        break # Network down at startup, break while loop to allow GUI to form
                    lbl7.config(text="Speedtest failed - retry in 1 min", bootstyle=WARNING)
                waitandblink(60)

            # If Ubidots upload is enabled, prepare and send upload
            if ubidots_enabled and do_ubidots:
                if net_status:
                    if loggingfile: logging.debug('Speed-Net_status = TRUE. Attempting to send data to UbiDots')
                else:
                    if loggingfile: logging.debug('Speed-Net_status = FALSE, Attempting to send data to UbiDots, Download = %s', round(bw_down,2))
                payload = {VARIABLE_LABEL_1: round(bw_up, 2),
                    VARIABLE_LABEL_2: round(bw_down, 2),
                    VARIABLE_LABEL_3: round(ping_time,  2)}
                post = post_request(payload) # Send payload data to Ubidots, returned post will be Boolean True or False showing success or failure

        # While loop continues to run if speedtest failed or is below threshold until i exceeds three attempts
        t0=mtime()
        if loggingfile: logging.debug('Speed-Checking internet - down?: %s, Outage reported = %s',internet_down, internet_outage_reported)
        if internet_down:
            if internet_outage_reported:
                internet_outage_reported = True
            else:
                if loggingfile: logging.warning('>>>>>> Speed-Internet outage recorded at %s \n',time.strftime("%H:%M:%S %m %d,%Y"))
                internet_outage_reported = True
        else:
            if internet_outage_reported:
                if loggingfile: logging.warning('>>>>>> Speed-Internet is back up as of %s \n',time.strftime("%H:%M:%S %m %d,%Y"))
                internet_outage_reported = False
        return  
        ##End of speedtest function##

    def time_display():
        global bwd
        global bwu
        global bw_down
        global bwdevents
        global bwuevents
        global adl24
        global adu24
        global bw_up
        global post
        global net_status
        global timestamp2 # Day of month from database
        global ping_time    # Last test ping result
        global last_tested  # Date & Time of last successful test
        global last_dbindex
        global dbindex
        global ubidots_enabled
        global opscounter
        global loggingfile
        test_time = current_time
        lasttime = time.localtime()
        today = datetime.datetime.now()  # Get today's day of the month 
        timestamp1 = today.strftime("%d") # Timestamp1 will be integer day of month (1-31)
        if loggingfile: logging.debug('Time Display Function (TDF) - Reading database')
        timestamp2 = read_db()  # Read information stored in database
        if timestamp1 != timestamp2: # If not equal, today is a different day from first item stored in database
            for i in range(29, 0, -1):
                bwu[i] = bwu[i-1] # Rotate bw_upload speed results one day to the right to make room for new upload data in position zero
                bwd[i] = bwd[i-1] # Rotate download speeds results same as ping data
        bwu[0] = int(bw_up) # Insert today's bw_upload value into first cell and move prior values one cell to the right
        bwd[0] = int(bw_down) # Same for upload value but these will be changed to average values - see below
        if loggingfile: logging.debug('Time Display Function - BW-Down = %d, BW-Up = %d', bw_down, bw_up)
        houroftest = int(time.strftime("%H",last_tested))
        minoftest = int(time.strftime("%M", last_tested))
        if loggingfile: logging.debug('TDF-Hour = %s, Min = %s', houroftest, minoftest)
        minindex = 0
        if (0 <= minoftest <= 29):
            minindex = 0
        elif (30 <= minoftest <= 59):
            minindex = 1
        dbindex = houroftest*2 + minindex # One test approx every 30 min = 2 tests per hour
        if (last_dbindex > dbindex):
            if (last_dbindex < 48):
                for i in range(last_dbindex+1,48,1):
                    bwdevents[i] = 0
                    bwuevents[i] = 0
                for i in range(0, dbindex,1):
                    bwdevents[i] = 0
                    bwuevents[i] = 0
        elif (dbindex - last_dbindex >1):
            if (dbindex != 0):
                for i in range(last_dbindex+1,dbindex,1):
                    bwdevents[i] = 0
                    bwuevents[i] = 0
        if loggingfile: logging.debug('TDF-LastDBIndex = %d, NewDBIndex = %d',last_dbindex, dbindex)
        last_dbindex = dbindex
        bwdevents[dbindex] = int(bw_down) 
        bwuevents[dbindex] = int(bw_up)
        if loggingfile: logging.debug('TDF-OpsCounter = %d, Hour = %s, Test %s, Current downloadspeed = %s', opscounter, houroftest, minindex+1, bwdevents[dbindex])
        zerodcount=0
        zeroucount=0
        for i in range(0,48,1):  # Remove zero entries from averages of download and upload speeds
            if bwdevents[i] == 0:
                zerodcount = zerodcount+1
            if bwuevents[i] == 0:
                zeroucount = zeroucount+1
        countdownnotzero = len(bwdevents)-zerodcount
        countupnotzero = len(bwuevents)-zeroucount
        adl24 = int(sum(bwdevents)/countdownnotzero)  # Average speedtest downloads over last 24 hours (ignoring zero cases)
        adu24 = int(sum(bwuevents)/countupnotzero)  # Average speedtest uploads over last 24 hours (ignoring zero cases)
        if loggingfile: logging.debug('TDF-24 Hr Average of Download speed = %d, Upload speed = %d', adl24, adu24)
        bwd[0] = adl24 # Sets number for today's download to average of last 24 hours
        bwu[0] = adu24 # Sets number for today's upload to average of last 24 hours
        if loggingfile: logging.debug('TDF-Average BW-Down = %d, BW-up = %d', adl24, adu24)
        if loggingfile: logging.debug('TDF-Writing database')
        write_db(timestamp1) # Store updated data in database
        for widget in frame4.winfo_children():  # Clear's status frame of prior messages
            widget.destroy()
        fnt = font.Font(family='Helvetica', size=20)
        if net_status: #net_status true means download speed was above minimum threshold
            lbl7.config(text='Internet is !GOOD!', bootstyle=SUCCESS)
        else:
            lbl7.config(text='Internet is !DOWN!', bootstyle=WARNING)
            lbl8 = ttk.Label(frame4, text='Internet down at: ', font=fnt, bootstyle=WARNING)
            lbl8.place(x=0, y=48, anchor=NW)
            lbl16 = ttk.Label(frame4, text=current_time, font=fnt, bootstyle=WARNING)
            lbl16.place(x=0, y=104, anchor=NW)
        if ubidots_enabled:
            if not post: # If post is False, Ubidots update failed
                lbl19=ttk.Label(frame4, text='Ubidots update Failed', font=fnt, bootstyle=WARNING)
                lbl19.place(x=0, y=158, anchor=NW)
        else:
            lbl19=ttk.Label(frame4, text='Ubidots is disabled', font=fnt, bootstyle=SUCCESS)
            lbl19.place(x=0, y=158, anchor=NW)
        return
        ##End of time_display function##
        
    def meters():
        global ping_time
        global bw_down
        global bw_up
        global maxdlmeter
        global maxulmeter
        global maxpingmeter
        global loggingfile

        if loggingfile: logging.debug('Meters Function - Building meters')
        ping_meter = ttk.Meter(frame2, bootstyle='warning', metersize=288, stripethickness=10, amountused=ping_time,
                           amounttotal=maxpingmeter, padding=5, subtext='Ping', metertype='semi',
                           interactive=False, textright='ms').grid(sticky=N, row=0, column=2, padx=5, pady=5)
        download_meter = ttk.Meter(frame2, metersize=288, stripethickness=10, amountused=bw_down, amounttotal=maxdlmeter,
                                subtext='Download Speed', padding=5, metertype='semi', interactive=False,
                               textright='MBps').grid(sticky=N, row=0, column=0, padx=5, pady=5)
        upload_meter = ttk.Meter(frame2, metersize=288, stripethickness=10, amountused=bw_up, amounttotal=maxulmeter,
                             bootstyle='success', padding=5, subtext='Upload Speed', metertype='semi',
                             interactive=False, textright='MBps').grid(sticky=N, row=0, column=1, padx=5, pady=5)
        fnt = font.Font(family='Helvetica', size=18)
        lbl10 = ttk.Label(frame2, text=('Download max-' + str(maxdlmeter) + 'MBps'), font=fnt, bootstyle=INFO)
        lbl10.place(x=18, y=280, anchor=NW)
        lbl11 = ttk.Label(frame2, text=('Upload max-' + str(maxulmeter) + 'MBps'), font=fnt, bootstyle=INFO)
        lbl11.place(x=328, y=280, anchor=NW)
        lbl12 = ttk.Label(frame2, text=('Ping max-' + str(maxpingmeter) + 'ms'), font=fnt, bootstyle=INFO)
        lbl12.place(x=648, y=280, anchor=NW)
        lbl13 = ttk.Label(frame2, text='Last tested:', font=fnt, bootstyle=INFO)
        lbl13.place(x=18, y=320, anchor=NW)
        lbl14 = ttk.Label(frame2, text=time.strftime("%Y-%m-%d %H:%M", last_tested), font=fnt, bootstyle=INFO)
        lbl14.place(x=160, y=320, anchor=NW)
        return
        ##End of meters function##

    def bar_chart():
        global bwd
        global bwu
        global bwdevents
        global adl24
        global adu24
        global dbindex
        global loggingfile

        for widget in frame3.winfo_children():  # Clear's bar chart frame
            widget.destroy()
        for widget in frame5.winfo_children():  # Clear frame 5 for 12 hour bar chart
            widget.destroy()
        ind = numpy.arange(30)
        ind2 = numpy.arange(48)

        # Build 30 day barchart
        if loggingfile: logging.debug('Bar Chart Function - Building bar charts')
        width = 0.4
        matplotlib.use("TkAgg")
        f = Figure(figsize=(7,1.6), dpi=120)
        ax = f.add_subplot(111)
        ax2 = ax.twinx() # Create second axis
        rects1 = ax.bar(ind, bwu, width, color = 'orange')
        rects2 = ax2.bar(ind+width, bwd, width, color = 'blue')
        ax.set_xticks([0.2,5.2,10.2,15.2,20.2,25.2,30.2])
        ax.set_xticklabels(('Today','D-5','D-10','D-15','D-20','D-25','D-30'))
        ax.set_ylabel('Up speed (MBps)', color = 'orange')
        ax2.set_ylabel('Down speed (MBps)', color = 'blue')
        ax.grid(True)
        f.tight_layout()
        canvas = FigureCanvasTkAgg(f, master=frame3)
        canvas.get_tk_widget().pack(expand=1)
        canvas.draw()
        lbl17 = ttk.Label(root, text='Thirty day history of speedtests', bootstyle=INFO, font=("Helvetica", 18))
        lbl17.place(x=940, y=690, anchor=CENTER)

        # Build 24-hour barchart
        width2 = 0.6
        f3 = Figure(figsize=(5,1.6), dpi=120)
        ax3 = f3.add_subplot(111)
        rects3 = ax3.bar(ind2, bwdevents, width, color = 'blue')
        rects4 = ax3.bar(dbindex, bwdevents[dbindex], width2, color = 'orange')
        ax3.set_xticks([0, 12, 24, 36,  48])
        ax3.set_xticklabels(('MidN', '6am', 'Noon', '6pm', 'MidN'))
        ax3.set_ylabel('Downspeed (MBps)', color = 'blue')
        ax3.grid(True)
        f3.tight_layout()
        canvas2 = FigureCanvasTkAgg(f3, master=frame5)
        canvas2.get_tk_widget().pack(expand=1)
        canvas2.draw()
        lbl18 = ttk.Label(root, text=('24-Hr Down Avg = ' + str(adl24) + ', Up Avg = ' + str(adu24) + 'MBps'), bootstyle=INFO, font=("Helvetica", 18))
        lbl18.place(x=280, y=690, anchor=CENTER)
        return
        ##End of bar_chart function##

    # Remainder of Update_Speedtest function
    # Check for speedtest failure or pause speedtests and run ping tests
    if loggingfile: logging.debug('Update Speedtest function (USF). Starting speedtest update, checking bw_down = %d',bw_down)
    LED_onoff("blue",False)
    speedtest_start=False
    if loggingfile: logging.info('USF-Speedtest_ready variable is %s', speedtest_ready)
    if speedtest_ready:
        #Begin speedtest
        if loggingfile: logging.info('USF-Calling speed function')
        speed() # Calling speedtest function
        current_time = time.strftime("%H:%M:%S, %d.%m.%Y")
        last_tested = time.localtime()
        opscounter = opscounter + 1
        speedtest_ready=False
        if loggingfile: logging.debug('USF-Opscounter updated - opscycle = %d',opscounter)
        if loggingfile: logging.debug('USF-Calling time_display function')
        time_display() # Calling time_display function
        if loggingfile: logging.debug('USF-Calling meters function')
        meters() # Calling meters display function
        if loggingfile: logging.debug('USF-Calling bar chart function')
        bar_chart() # Calling bar chart function
        txt = ('Cycle ' + str(opscounter) + ' Booted ' + time.strftime("%b %d-%H:%M", timestart))
        lbl9=ttk.Label(root, text=txt, font=('Helvetica', 18), bootstyle=INFO)
        lbl9.place(x=16, y=440, anchor=NW)
        if loggingfile: logging.debug('USF-GUI Updated. Ops counter = %s', opscounter)
        if bw_down < lower_limit:  # Test for speedtest failure
            mindelay = 1
            secdelay = 60
            if loggingfile: logging.warning('>>>>>> USF-bw_down is less than limit, retest in %d seconds \n',secdelay)
        else:
            mindelay = int(timedelay/60)
            secdelay = timedelay
            if loggingfile: logging.debug('USF-bw_down records successful speedtest, retest in %d minutes',mindelay)
        if loggingfile: logging.debug('USF-List of threads before starting new thread  = %s',str(threading.enumerate()))
        countdown_thread_name = "Thread-"+time.strftime("%H:%M")
        if loggingfile: logging.debug('USF-Threadname is %s and type is %s',countdown_thread_name, type(countdown_thread_name))
        countdown_thread = threading.Thread(target=countdown, args=(secdelay,), name = countdown_thread_name)
        countdown_thread.start()
        if loggingfile: logging.debug('USF-Countdown thread started, calling monitor function after program summary')
        test=0
        if loggingfile:
            logging.info('**********')
            logging.info('Program summary: opscounter cycle = %d, GUI has been updated',opscounter)
            logging.info('Program summary: last download speed = %d MBPS, last upload speed = %d MBPS',bw_down, bw_up)
            logging.info('Program summary: average download last 24 hrs = %d, average upload = %d MBPS',adl24, adu24)
            logging.info('Program summary: internet is down? %s',internet_down)
            logging.info('Program summary: historical data for last 24 hours and last 30 days are recorded in bandwidth3.db')
            logging.info('Program summary: thread list before starting monitor = %s',str(threading.enumerate()))
            if goodping:
                logging.info('Program summary: pings to Google at last attempt were working fine')
            logging.info('********** \n')
        time.sleep(5)
        root.after(10000,lambda:monitor(countdown_thread, countdown_thread_name)) #Anonymous call to monitor function, passing countdown_thread
        ##End of Update_Speedtest function##

def write_db(day):  # Function to store all data to database
    global bwd
    global bwu
    global bwdevents
    global bwuevents
    global last_dbindex
    global ping_time
    global routerdelay
    global modemdelay
    global relays_enabled
    global ubidots_enabled
    global maxdlmeter
    global maxulmeter
    global maxpingmeter
    global max_iterations
    global lower_limit
    global pingtestdelay
    global database_def
    global database
    global loggingfile

    file=open(database,"w")
    file.write(database_def[0] + "\n")
    file.write(str(day) + "\n")
    file.write(database_def[1] + "\n")
    for i in range(0,30,1):
        file.write(str(bwu[i])+"\n")
    file.write(database_def[2] + "\n")
    for i in range(0,30,1):
        file.write(str(bwd[i])+"\n")
    file.write(database_def[3] + "\n")
    for i in range(0,48,1):
        file.write(str(bwdevents[i])+"\n")
    file.write(database_def[4] + "\n")
    for i in range(0,48,1):
        file.write(str(bwuevents[i])+"\n")
    file.write(database_def[5] + "\n")
    file.write(str(last_dbindex)+"\n")
    file.write(str(routerdelay)+"\n")
    file.write(str(modemdelay)+"\n")
    file.write(str(relays_enabled)+"\n")
    file.write(str(ubidots_enabled)+"\n")
    file.write(str(maxdlmeter)+"\n")
    file.write(str(maxulmeter)+"\n")
    file.write(str(maxpingmeter)+"\n")
    file.write(str(max_iterations)+"\n")
    file.write(str(lower_limit)+"\n")
    file.write(str(pingtestdelay)+'\n')
    file.write(str(loggingfile)+'\n')
    file.close
    return
    ##End of write_db function##

def read_db():  # Function to read all stored data from database
    global bwd
    global bwu
    global bwdevents
    global last_dbindex
    global routerdelay
    global modemdelay
    global relays_enabled
    global ubidots_enabled
    global maxdlmeter
    global maxulmeter
    global maxpingmeter
    global max_iterations
    global lower_limit
    global pingtestdelay
    global database_def
    global database
    global loggingfile

    timestamp = 0
    list=[]
    file=open(database,"r")
    file_lines=file.read()
    list=file_lines.split("\n")
    file.close
    timestamp = list[1] #Must be a string for comparison to today
    for i in range(0, 30, 1):
        bwu[i] = int(float(list[i+3]))
        bwd[i] = int(float(list[i+34]))
    for i in range(0, 48, 1):
        bwdevents[i] = int(float(list[i+65]))
        bwuevents[i] = int(float(list[i+114]))
    last_dbindex = int(float(list[163]))
    routerdelay = int(float(list[164]))
    modemdelay = int(float(list[165]))
    if (list[166] <= "True"):
        relays_enabled = True
    else:
        relays_enabled = False
    if (list[167] == "True"):
        ubidots_enabled = True
    if (list[167] == "False"):
        ubidots_enabled = False
    maxdlmeter = int(float(list[168]))
    maxulmeter = int(float(list[169]))
    maxpingmeter = int(float(list[170]))
    max_iterations = int(float(list[171]))
    lower_limit = int(float(list[172]))
    pingtestdelay = int(float(list[173]))
    if (list[174] <= "True"):
        loggingfile = True
    else:
        loggingfile = False
    return timestamp
    ##End of read_db function##

def countdown(t):
    # Delay timer for next speedtest. Pings to Google DNS server every minute. If ping fails, system will attempt speedtest
    global goodping
    global ip_list
    global pingtestdelay
    global loggingfile
    start = int(mtime()) #Monotomic time in seconds
    finish = t + start   #Countdown end in seconds for comparison to mtime()
    pingcount = 0 # Tracks failures occuring in a row
    if loggingfile:
        logging.debug('Countdown thread. Starting delay for next speedtest to be run in %d minutes',t/60)
        logging.debug('Countdown thread. Start = mtime() = %d. Finish = %d.', start/60, finish/60)
        logging.debug('Countdown thread. Pings will be done every %d seconds', pingtestdelay)
    while int(mtime()) < finish:
        if loggingfile: logging.debug('Countdown thread. Trying ping test')
        response = ping_test()
        if loggingfile:
            logging.debug('Countdown thread. Ping test response = %s',response)
            logging.info('Countdown thread. Remaining minutes to next speedtest = %d', int((finish-mtime())/60))
        if goodping:
            pingcount = 0
            if loggingfile: logging.info('Countdown thread. Ping successful, going to sleep for %d seconds',pingtestdelay)
            time.sleep(pingtestdelay)
        else:
            if pingcount >= 3:
                if loggingfile: logging.warning('>>>>>> Countdown thread. 3 Ping failures in a row, killing countdown thread and starting speedtest after 30 sec \n')
                root.update_idletasks()
                time.sleep(30)
                if loggingfile: logging.debug('Countdown thread. Sleep delay over, terminating thread')
                countdown_thread.kill()
                break # End thread - pings and function will cease
            else:
                pingcount += 1
                if loggingfile: logging.debug('Countdown thread. Ping failure, iteration count = %d', pingcount)
    ##End of countdown function##

def ping_test():
    global goodping
    global loggingfile
    try:
        response = str(ping(ip_list, count=1, verbose=False))
        if "Reply from" in response:
            goodping = True
            if loggingfile: logging.debug('PTF-Ping_test. Ping successful')
        else:
            goodping = False
            if loggingfile: logging.warning('>>>>>> PTF-Ping_test. Ping unsuccessful, response=%s \n',response)
    except Exception as e:
        if loggingfile: logging.warning('>>>>>> PTF-Ping test failure, report = %s \n',e)
        goodping=False
    return response
    ##End of ping_test function##

def monitor(countdown_thread, threadname):
    global speedtest_ready
    global test
    global countdown_thread_name
    global loggingfile

    speedtest_ready = False
    list=str(threading.enumerate())
    char_pos=list.find('Thread-')
    thread_name = list[char_pos:char_pos+12]
    if loggingfile:
        logging.debug('Monitor-Thread enumerate() is %s and type is %s',list, type(list))
        logging.debug('Monitor-Threadname recovered from enumerate() is %s and type is %s',thread_name, type(thread_name))
        logging.debug('Monitor-Threadname received through function call is %s',threadname)
    if (thread_name == threadname) or (test < 2):
        test = test +1
        if test < 2:
            if loggingfile: logging.info('Monitor-Test %d, thread names are equal (%s), restarting monitor for next test in 20 sec',test,thread_name)
        root.update_idletasks()
        root.after(20000,lambda:monitor(countdown_thread,threadname)) #Cycles through this function until countdown thread is finished
    else:
        if loggingfile: logging.info('Monitor-Detected end of Countdown Thread. Starting new speedtest cycle after %d tests',test)
        speedtest_ready=True
        update_speedtest()
    ##End of monitor function##

def sysmenu(): # System Options Menu for changing key parameters
    global relays_enabled
    global routerdelay
    global modemdelay
    global ubidots_enabled
    global loggingfile
    global TOKEN
    global intnum
    global boolval
    global check_1
    global check_2
    global check_3
    global entrynum1
    global entrynum2
    global entrynum3
    global entrynum4
    global entrynum5
    global entrynum6
    global entrynum7
    global entrynum8
    global maxdlmeter
    global maxulmeter
    global maxpingmeter
    global max_iterations
    global lower_limit
    global pingtestdelay

    def getrelaychk():
        global relays_enabled
        global check_1
        if check_1.get() == True:
            relays_enabled = True
        else:
            relays_enabled = False
        if loggingfile: logging.info('Relays_enabled changed -  now is %s',relays_enabled)
    ##End of getrelaychk function##

    def getubichk():
        global ubidots_enabled
        global check_2
        if check_2.get() == True:
            ubidots_enabled = True
        else:
            ubidots_enabled = False
        if loggingfile: logging.info('Ubidots_enabled changed - now is %s', ubidots_enabled)
    ##End of getubichk function##

    def getloggingchk():
        global loggingfile
        global check_3
        if check_3.get() == True:
            loggingfile = True
        else:
            loggingfile = False
        if loggingfile: logging.info('Logging option changed - now is %s', loggingfile)
    ##End of getloggingchk function##

    def getrouternum(num):
        global routerdelay
        global entrynum1
        routerdelay = int(entrynum1.get())
        if loggingfile: logging.info('Router delay changed - now is %d', routerdelay)
    ##End of getrouternum function##

    def getmodemnum(num):
        global modemdelay
        global entrynum2
        modemdelay = int(entrynum2.get())
        if loggingfile: logging.info('Modem delay changed - now is %d', modemdelay)
    ##End of getmodemnum function##

    def getmaxdlmeter(num):
        global maxdlmeter
        global entrynum3
        maxdlmeter = int(entrynum3.get())
        if loggingfile: logging.info('Max download speed for meter changed - now is %d', maxdlmeter)
    ##End of getmaxdlmeter function##

    def getmaxulmeter(num):
        global maxulmeter
        global entrynum4
        maxulmeter = int(entrynum4.get())
        if loggingfile: logging.info('Max upload speed for meter changed - now is %d', maxulmeter)
    ##End of getmaxulmeter function##

    def getmaxpingmeter(num):
        global maxpingmeter
        global entrynum5
        maxpingmeter = int(entrynum5.get())
        if loggingfile: logging.info('Max ping speed for meter changed - now is %d', maxpingmeter)
    ##End of getmaxpingmeter function##

    def getmaxiterations(num):
        global max_iterations
        global entrynum6
        max_iterations = int(entrynum6.get())
        if loggingfile: logging.info('Max iterations for speedtest changed - now is %d', max_iterations)
    ##End of getmaxiterations function##

    def getlowerlimit(num):
        global lower_limit
        global entrynum7
        lower_limit = int(entrynum7.get())
        if loggingfile: logging.info('Lower limit (MBps) threshold for speedtest changed - now is %d', lower_limit)
    ##End of getlowerlimit function##

    def getpingtestdelay(num):
        global pingtestdelay
        global entrynum8
        tempnum = pingtestdelay
        pingtestdelay = int(entrynum8.get())
        if loggingfile: logging.info('Ping test delay changed - was %d, now is %d', tempnum, pingtestdelay)
    ##End of getpingtestdelay function##

    def validate_number(x) -> bool:
        """ Validates that the input is a number """
        if x.isdigit():
            return True
        elif x == "":
            return True
        else:
            return False
    ##End of validate_number function##

    def closethewindow():
        timestamp1 = today.strftime("%d") # Get today's day of the month
        write_db(timestamp1) # Rewrite database with new configuration
        if loggingfile: logging.info('System Menu closed, data updated in database')
        menu.destroy()
    ##End of closethewindow function##

    # Build menu for changing parameters
    menu = ttk.Toplevel(title="System Options Menu", size=[800, 600])
    menu.attributes("-topmost", True)
    menu.resizable(True, True)
    menu.bind("<Escape>", quit)
    check_1 = BooleanVar(value=relays_enabled)
    check_2 = BooleanVar(value=ubidots_enabled)
    check_3 = BooleanVar(value=loggingfile)
    entrynum1 = IntVar(value=routerdelay)
    entrynum2 = IntVar(value=modemdelay)
    entrynum3 = IntVar(value=maxdlmeter)
    entrynum4 = IntVar(value=maxulmeter)
    entrynum5 = IntVar(value=maxpingmeter)
    entrynum6 = IntVar(value=max_iterations)
    entrynum7 = IntVar(value=lower_limit)
    entrynum8 = IntVar(value=pingtestdelay)

    fnt = font.Font(family='Helvitica', size=16)
    lbl32 = ttk.Label(menu, text = 'System Options Menu - Adjust changes to key parameters', font=fnt, bootstyle = "info")
    lbl32.place(x=100, y=20)
    fnt = font.Font(family='Helvitica', size=12)
    if loggingfile: logging.info('Systems Menu opened for changes')

    # Relay enabled check
    relaychk = ttk.Checkbutton(menu, text='Enable Relays', variable=check_1, onvalue=True, offvalue=False, 
        bootstyle="primary-round-toggle", command= lambda: getrelaychk())
    relaychk.place(x=20, y=58)

    # Enter router and modem reboot time in seconds and validate numeric entries
    lbl30 = ttk.Label(menu, text='Enter router boot time (sec) + CR', font=fnt, bootstyle="info")
    lbl30.place(x=20, y=100)
    routernum_entry = ttk.Entry(menu, textvariable=entrynum1)
    routernum_entry.bind('<Return>',getrouternum)
    routernum_entry.place(x=320, y=100, width=90)

    lbl31 = ttk.Label(menu, text='Enter modem boot time (sec) + CR', font=fnt, bootstyle="info")
    lbl31.place(x=20, y=150)
    modemnum_entry = ttk.Entry(menu, textvariable=entrynum2)
    modemnum_entry.bind('<Return>',getmodemnum)
    modemnum_entry.place(x=320, y=150, width=90)

    # Ubidots option check button
    ubidotchk = ttk.Checkbutton(menu, text='Enable Ubidots Upload', variable=check_2, onvalue=True, offvalue=False, 
        bootstyle="primary-round-toggle", command= lambda: getubichk())
    ubidotchk.place(x=20, y=200)
    lbl33 = ttk.Label(menu, text="Ubidots Token = " + TOKEN, font=fnt, bootstyle="info")
    lbl33.place(x=20, y=250)

    # Logging option
    loggingcheck = ttk.Checkbutton(menu, text='Enable Logging', variable=check_3, onvalue=True, offvalue=False,
        bootstyle="primary-round-toggle", command= lambda: getloggingchk())
    loggingcheck.place(x=20, y=310)

    # Meter parameters
    lbl34 = ttk.Label(menu, text='Meter max limit parameters + CR', font=fnt, bootstyle="info")
    lbl34.place(x=450, y=50)
    lbl35 = ttk.Label(menu, text='Max Download Speed (MBps)')
    lbl35.place(x=450, y=100)
    maxdlmeter_entry = ttk.Entry(menu, textvariable=entrynum3)
    maxdlmeter_entry.bind('<Return>',getmaxdlmeter)
    maxdlmeter_entry.place(x=700, y=100, width=90)
    lbl36 = ttk.Label(menu, text='Max Upload Speed (MBps)')
    lbl36.place(x=450, y=150)
    maxulmeter_entry = ttk.Entry(menu, textvariable=entrynum4)
    maxulmeter_entry.bind('<Return>',getmaxulmeter)
    maxulmeter_entry.place(x=700, y=150, width=90)
    lbl37 = ttk.Label(menu, text='Max Ping Speed (Sec)')
    lbl37.place(x=450, y=200)
    maxpingmeter_entry = ttk.Entry(menu, textvariable=entrynum5)
    maxpingmeter_entry.bind('<Return>',getmaxpingmeter)
    maxpingmeter_entry.place(x=700, y=200, width=90)

    #Speetest parameters
    fnt = font.Font(family='Helvitica', size=16)
    lbl38 = ttk.Label(menu, text = 'Speedtest parameters', font=fnt)
    lbl38.place(x=450, y=300)
    fnt = font.Font(family='Helvitica', size=12)
    lbl39 = ttk.Label(menu, text = 'Speedtest max iterations', font=fnt)
    lbl39.place(x=450, y=350)
    maxiterations_entry = ttk.Entry(menu, textvariable=entrynum6)
    maxiterations_entry.bind('<Return>', getmaxiterations)
    maxiterations_entry.place(x=700, y=350, width=90)
    lbl40 = ttk.Label(menu, text = 'Speedtest lower limit (MBps)', font=fnt)
    lbl40.place(x=450, y=400)
    lowerlimit_entry = ttk.Entry(menu, textvariable=entrynum7)
    lowerlimit_entry.bind('<Return>', getlowerlimit)
    lowerlimit_entry.place(x=700, y=400, width=90)

    # Pingtestdelay
    fnt = font.Font(family='Helvitica', size=12)
    lbl41 = ttk.Label(menu, font=fnt, text = 'Time between simple ping tests (sec) + CR')
    lbl41.place(x=20, y=350)
    pingtestdelay_entry = ttk.Entry(menu, textvariable=entrynum8)
    pingtestdelay_entry.bind('<Return>', getpingtestdelay)
    pingtestdelay_entry.place(x=320, y=350, width=90)

    # Kill switch
    killbutton = ttk.Button(menu, text="Kill Program", command=quit, bootstyle="danger")
    killbutton.place(x=200, y=550, anchor=NW)

    #Close button to close window
    closebutton = ttk.Button(menu, text="Close Window", command=closethewindow, bootstyle="warning")
    closebutton.place(x=500, y=550)
    ##End of sysmenu function##

# Set up Root (main) window

root = ttk.Window(themename="litera", title="Internet Monitor",size=[1280, 800], position=None)
root.attributes('-fullscreen', True)
root.focus_force()
root.geometry('1280x768')
root.resizable(False, False)
root.bind("<Escape>", quit)  # Sets Escape key to stop tKinter GUI
root.bind("x", quit)
style = ttk.Style()

# Set up time stamps
fnt = font.Font(family='Helvetica', size=24)
lbl1 = ttk.Label(root, text='Current time: ', font=fnt, bootstyle = INFO)
lbl1.place(x=16, y=40, anchor=NW)
now = time.localtime()
txt = time.strftime("%H:%M:%S", now)
lbl2 = ttk.Label(root, text=txt, font=fnt, bootstyle=INFO)
lbl2.place(x=224, y=40, anchor=NW)

# Set up frames
frame1 = ttk.Frame() # Frame for screen title
frame1.pack(fill=BOTH, expand=True)
frame1.place(x=432, y=20, width=720, height=120, anchor=NW)
frame2 = ttk.Frame() # Frame for meters
frame2.pack(fill=BOTH, expand=True)
frame2.place(x=336, y=140, width=928, height=400, anchor=NW)
frame3 = ttk.Frame() # Frame for bar chart at bottom of screen
frame3.pack(fill=BOTH, expand=True)
frame3.place(x=532, y=490, width=716, height=210, anchor=NW)
frame4 = ttk.Frame()  # Frame for status messages
frame4.pack(fill=BOTH, expand=True)
frame4.place(x=16, y=96, width=320, height=240)
frame5 = ttk.Frame()  # Frame for hourly download speeds
frame5.pack(fill=BOTH, expand=True)
frame5.place(x=32, y=490, width=495, height=210, anchor=NW)
fnt = font.Font(family='Helvetica', size=20)
lbl7 = ttk.Label(root, text='Network status pending', font=fnt, bootstyle=SUCCESS)
lbl7.place(x=16, y=96, anchor=NW)

# Screen title label
fnt = font.Font(family='Helvetica', size=46)
lbl3 = ttk.Label(frame1, text='The Internet Monitor', font=fnt, bootstyle=PRIMARY)
lbl3.place(x=24, y=16, anchor=NW)
fnt = font.Font(family='Helvetica', size=16)
lbl4 = ttk.Label(frame1, text=author, font=fnt, bootstyle=PRIMARY)
lbl4.place(x=640, y=120, anchor=SE)
lbl5 = ttk.Label(frame1, text=version, font=fnt, bootstyle=PRIMARY)
lbl5.place(x=24, y=120, anchor=SW)

# Display retest button & time display
timer = '30:00'
fnt = font.Font(family='Helvetica', size=18)
lbl20 = ttk.Label(root, text='Time to next speedtest ', font=fnt, bootstyle=INFO)
lbl20.place(x=16, y=380, anchor=NW)
lbl21 = ttk.Label(root, text=timer, font=fnt, bootstyle=INFO)
lbl21.place(x=270, y=380, anchor=NW)

# Install system menu button
if loggingfile: logging.debug('Installing system menu button')
style = ttk.Style()
style.configure('TButton', font=('Helvetica', 16))
systemmenu = ttk.Button(root, text="Options", command=sysmenu)
systemmenu.place(x=1100, y=10, height=80, width=150, anchor=NW)

# Button for conducting manual speed test
if loggingfile: logging.debug('Installing manual speedtest button')
style = ttk.Style()
style.configure('TButton', font=('Helvetica', 16))
manualtestbutt = ttk.Button(root, text="Press for Speed Test or wait", command=start_speedtest)
manualtestbutt.place(x=16, y=300, height=50, width=320,  anchor=NW)

# Update clock time every 1 sec
root.after(10, lambda:update_clock())  # schedule update_clock function

# Launch speedtest function (self sustaining)
if speedtest_start:  # Kickoff speedtest
    speedtest_start=False
    update_speedtest()

root.mainloop()
