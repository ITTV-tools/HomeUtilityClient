#!/usr/bin/python

import paho.mqtt.client as paho
import time
from Adafruit_MCP230xx import Adafruit_MCP230XX
from threading import Thread
import ConfigParser
import RPi.GPIO as GPIO

Config = ConfigParser.ConfigParser()
Config.read("ShutterControl.ini")

#---------------Settings----------------------
# [ID, Name, Time to Move, StateNow, GPIOUp, GPIODown, Mode, LEDPIN, TargetTime]
Shutters = [[1, "Wohnzimmer", 21.1, 1.1,  7, 6, 0, 13, 0],[2, "Esszimmer", 30.1, 0,  5, 4, 0, 14, 0], [3, "Esszimmer2", 22.3, 0,  3, 2, 0, 15, 0]]
#[UP, Stop, down, left(previous), right(next)]
Buttons = [8, 9, 10, 11, 12]
#--------------------------------------------
mcp = Adafruit_MCP230XX(busnum = 1, address = 0x20, num_gpios = 16)

GPIO.setmode(GPIO.BCM)
channel = 21
GPIO.setup(channel, GPIO.IN, pull_up_down = GPIO.PUD_UP)
  # add rising edge detection on a channel

def test(channel):
    print("button press")

GPIO.add_event_detect(channel, GPIO.RISING, callback = test, bouncetime = 250)

def ConfigSectionMap(section):
    dict1 = {}
    options = Config.options(section)
    for option in options:
        try:
            dict1[option] = Config.get(section, option)
            if dict1[option] == -1:
                DebugPrint("skip: %s" % option)
        except:
            print("exception on %s!" % option)
            dict1[option] = None
    return dict1

mqttServer = ConfigSectionMap("MQTT")['mqttserver']
mqttPort = ConfigSectionMap("MQTT")['mqttport']
mqttUsername = ConfigSectionMap("MQTT")['mqttusername']
mqttPassword = ConfigSectionMap("MQTT")['mqttpassword']

def ButtonControl():
    global Buttons
    global Shutters
    Select = 0
    LightingCounter = 0
    for button in Buttons:
        mcp.config(int(button), mcp.INPUT)
        mcp.pullup(int(button), 1)
        mcp.Interupts(int(button),1)
    for led in Shutters:
        mcp.config(led[7], mcp.OUTPUT)
        mcp.output(led[7], 0)
    while True:
        if(int(mcp.input(Buttons[0]) >> Buttons[0]) == 0):
            if(Select <= (len(Shutters) -1)):
                Shutters[Select][6] = 1
            else:
                for Shutter in Shutters:
                    Shutter[6] = 1
            LightingCounter = 0
        elif(int(mcp.input(Buttons[1]) >> Buttons[1]) == 0):
            if(Select <= (len(Shutters) -1)):
                Shutters[Select][6] = 0
            else:
                for Shutter in Shutters:
                    Shutter[6] = 0
            LightingCounter = 0
        elif(int(mcp.input(Buttons[2]) >> Buttons[2]) == 0):
            if(Select <= (len(Shutters) -1)):
                Shutters[Select][6] = 2
            else:
                for Shutter in Shutters:
                    Shutter[6] = 2
            LightingCounter = 0

        elif(int(mcp.input(Buttons[3]) >> Buttons[3]) == 0):
            LightingCounter = 0
            if(Select > 0):
                Select = Select - 1
            else:
                Select = (len(Shutters)-1) + 1

        elif(int(mcp.input(Buttons[4]) >> Buttons[4]) == 0):
            LightingCounter = 0
            if(Select < (len(Shutters)-1) + 1):
                Select = Select + 1
            else:
                Select = 0
        if(LightingCounter < 30):
            if(Shutters[0][6] == 0):
                LightingCounter = LightingCounter + 1
                if(Select < len(Shutters)):
                    for led in Shutters:
                        if(led[7] != Shutters[(Select)][7]):
                            mcp.output(led[7], 0)
                        else:
                            mcp.output(led[7], 1)
                else:
                    for led in Shutters:
                        mcp.output(led[7], 1)

        else:
            if(Shutters[0][6] == 0):
                for led in Shutters:
                    mcp.output(led[7], 0)
        time.sleep(0.3)

def ShutterControl():
    global Shutters
    while True:
        for Shutter in Shutters:
            if(Shutter[6] == 1) and (Shutter[3] < Shutter[2]):
                Shutters[Shutters.index(Shutter)][3] = round((Shutter[3] + 0.1), 2)
                mcp.output(int(Shutter[4]), 0)
                mcp.output(int(Shutter[5]), 1)
            elif(Shutter[6] == 2) and (Shutter[3] > 0):
                Shutters[Shutters.index(Shutter)][3] = round((Shutter[3] - 0.1), 2)
                mcp.output(int(Shutter[5]), 0)
                mcp.output(int(Shutter[4]), 1)
            elif(Shutter[6] == 0) or (Shutter[3] >= Shutter[2]) or (Shutter[3] <= 0):
                Shutters[Shutters.index(Shutter)][6] = 0
                mcp.output(int(Shutter[5]), 1)
                mcp.output(int(Shutter[4]), 1)
        time.sleep(0.1)


def on_subscribe(client, userdata, mid, granted_qos):
    print("Subscribed: "+str(mid)+" "+str(granted_qos))
    client.publish("Devices", payload="{12345:Connected}")

def on_message(client, userdata, msg):
    if(str(msg.payload) == "Update"):
        #StatusChange()
        print(msg.topic+" "+str(msg.qos)+" "+str(msg.payload))

def on_disconnect(client, userdata, rc):
    if rc != 0:
        print "Unexpected MQTT disconnection. Will auto-reconnect"

def on_connect(client, userdata, flags, rc):
    client.subscribe("Shutters", qos=1)


if __name__ == '__main__':
    print("Configured shutters:");
    for element in Shutters:
        print(element[1])
        mcp.config(int(element[4]), mcp.OUTPUT)
        mcp.config(int(element[5]), mcp.OUTPUT)
        mcp.output(int(element[4]), 1)
        mcp.output(int(element[5]), 1)

    t = Thread(target=ShutterControl)
    t2 = Thread(target=ButtonControl)
    t.setName("Shutter")
    t2.setName("Buttons")
    t.setDaemon(True)
    t.start()
    t2.setDaemon(True)
    t2.start()


    try:
        while True:
            client = paho.Client(client_id="12345" ,clean_session=False)
            client.username_pw_set(mqttUsername, mqttPassword)
            client.on_connect = on_connect
            client.on_subscribe = on_subscribe
            client.on_message = on_message
            client.will_set("Devices", payload="{12345:GONE}", qos=2, retain=False)
            client.connect(mqttServer, mqttPort)
            client.loop_forever()


    except (KeyboardInterrupt, SystemExit):
            client.publish("Devices", payload="{12345:GONE}")
            client.disconnect()
            print(" bye bye !")
