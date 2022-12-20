#! /usr/bin/env python
# * | File        :	  test_Relay.py
# * | Author      :   HoChri (aka Legufix)
# * | Function    :   Simple program to test the function of the relais
# * | Info        :
# *----------------
# * | This version:   V0.5 modified by Bart
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

RELAY_1 = 21
RELAY_2 = 22
GPIO.setup(RELAY_1,GPIO.OUT)
GPIO.output(RELAY_1,GPIO.HIGH)
GPIO.setup(RELAY_2, GPIO.OUT)
GPIO.output(RELAY_2,GPIO.HIGH)


if __name__ == "__main__":
    print ("Starting Relay Test")
    print ("Modem power will be cut in 5 sec")
    GPIO.output(RELAY_1,GPIO.LOW)
    print('Modem power cut')
    time.sleep(10)
    GPIO.output(RELAY_1,GPIO.HIGH)
    print("Modem power restored. Modem test finished")
    time.sleep(5)
    print("Relay power will be cut in 5 sec")
    time.sleep(5)
    GPIO.output(RELAY_2,GPIO.LOW)
    print("Router power cut")
    time.sleep(10)
    GPIO.output(RELAY_2,GPIO.HIGH)
    print("Router power restored")
    print("Relay test completed")
