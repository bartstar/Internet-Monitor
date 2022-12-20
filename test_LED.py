#! /usr/bin/env python
# * | File        :	  test_LED.py
# * | Author      :   HoChri (aka Legufix)
# * | Function    :   Simple program to test the function of the RGB LED
# * | Info        :
# *----------------
# * | This version:   V0.5, mofied by Bart
# * | Date        :   2022-12-18
#
# Modified to allow time between tests
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

import time
import RPi.GPIO as GPIO

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
GREEN = 5
BLUE = 6
RED = 13

GPIO.setup(GREEN,GPIO.OUT)
GPIO.setup(BLUE,GPIO.OUT)
GPIO.setup(RED,GPIO.OUT)
GPIO.output(GREEN,GPIO.LOW)
GPIO.output(BLUE,GPIO.LOW)
GPIO.output(RED,GPIO.LOW)



if __name__ == "__main__":
    print ("Starting LED Test")
    print ("Turning on GREEN")
    GPIO.output(GREEN,GPIO.HIGH)
    time.sleep(10)
    GPIO.output(GREEN,GPIO.LOW)
    print ("Turning on BLUE")
    GPIO.output(BLUE,GPIO.HIGH)
    time.sleep(10)
    GPIO.output(BLUE,GPIO.LOW)
    print ("Turning on RED")
    GPIO.output(RED,GPIO.HIGH)
    time.sleep(10)
    GPIO.output(RED,GPIO.LOW)
    print("Test finished")
