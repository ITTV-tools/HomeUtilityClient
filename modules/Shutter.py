#!/usr/bin/python
import time
from Adafruit_MCP230xx import Adafruit_MCP230XX
import RPi.GPIO as GPIO
import threading

class Shutter:
    __GPIOup = 7
    __GPIOdown = 6
    __MovingTime = 30
    __Position = 0
    __TargetPos = 0
    __Mode = "GPIO"

    def __init__(self, GPIOup, GPIOdown, Movingtime, Mode, Position=0):
        self.__GPIOup = GPIOup
        self.__GPIOdown = GPIOdown
        self.__MovingTime = Movingtime
        self.__Mode = Mode
        self.__Position = Position
        self.initGPIO()

    def initGPIO(self):
        if(self.__Mode == "GPIO"):
            GPIO.setwarnings(False)
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(self.__GPIOup, GPIO.OUT)
            GPIO.setup(self.__GPIOdown, GPIO.OUT)
            GPIO.output(self.__GPIOup, GPIO.HIGH)
            GPIO.output(self.__GPIOdown, GPIO.HIGH)
        elif(self.__Mode == "MCP230xx"):
            self.__mcp = Adafruit_MCP230XX(busnum = 1, address = 0x20, num_gpios = 16)
            self.__mcp.config(self.__GPIOup, self.__mcp.OUTPUT)
            self.__mcp.config(self.__GPIOdown, self.__mcp.OUTPUT)
            self.__mcp.output(self.__GPIOup, 1)
            self.__mcp.output(self.__GPIOdown, 1)
        self.__stop_event = threading.Event()
        self.__ShutterThread = threading.Thread(target=self.Act)
        self.__ShutterThread.daemon = True
        self.__ShutterThread.start()

    def GPIOhigh(self, PIN):
        if(self.__Mode == "GPIO"):
            GPIO.output(PIN, GPIO.HIGH)
        elif(self.__Mode == "MCP230xx"):
            self.__mcp.output(PIN, 1)

    def GPIOlow(self, PIN):
        if(self.__Mode == "GPIO"):
            GPIO.output(PIN, GPIO.LOW)
        elif(self.__Mode == "MCP230xx"):
            self.__mcp.output(PIN, 0)

    def moveShutterUp(self):
        self.GPIOlow(self.__GPIOup)
        self.GPIOhigh(self.__GPIOdown)

    def moveShutterDown(self):
        self.GPIOlow(self.__GPIOdown)
        self.GPIOhigh(self.__GPIOup)

    def stopShutter(self):
        self.GPIOhigh(self.__GPIOdown)
        self.GPIOhigh(self.__GPIOup)

    def Act(self):
        while (not self.__stop_event.is_set()):
            if(self.__TargetPos != self.__Position):
                if(self.__TargetPos < self.__Position):
                    self.__Position = round((self.__Position - 0.1), 2)
                    self.moveShutterUp()
                elif(self.__TargetPos > self.__Position):
                    self.__Position = round((self.__Position + 0.1), 2)
                    self.moveShutterDown()
                time.sleep(0.1)
            else:
                self.stopShutter()
                time.sleep(0.1)

#---------use this in your script

    def up(self):
        self.__TargetPos = 0

    def down(self):
        self.__TargetPos = self.__MovingTime

    def stop(self):
        self.__TargetPos = self.__Position

    def moveToPercent(self, percent):
        self.__TargetPos = (self.__MovingTime / 100 * percent)

    def getPositionInPercent(self):
        self.__TargetPos = round((100 * self.__Position / self.__MovingTime), 2)

    def disable(self):
        self.__stop_event.set()
