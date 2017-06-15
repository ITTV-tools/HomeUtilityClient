#!/usr/bin/python
import paho.mqtt.client as paho
import time
from threading import Thread
import json
import urllib
import RPi.GPIO as GPIO
import socket

#Conf
BaseURL = "http://172.31.1.205/php/Backend.php"

##

ip = [l for l in ([ip for ip in socket.gethostbyname_ex(socket.gethostname())[2] if not ip.startswith("127.")][:1], [[(s.connect(('8.8.8.8', 53)), s.getsockname()[0], s.close()) for s in [socket.socket(socket.AF_INET, socket.SOCK_DGRAM)]][0][1]]) if l][0][0]
hostname = socket.gethostname()



GPIOData = []
UpdateAvalible = []

GPIO.cleanup()
GPIO.setmode(GPIO.BCM)

def RefreshState(RolloID, StateNow):
    try:
        data = urllib.urlopen(BaseURL + "?Call=RefreshState&Rollo_ID=" + str(RolloID) + "&State_Now=" + str(StateNow))
    except urllib.error.HTTPError as e:
        print(e.code)
        print(e.read())
    print("Send new state for Rollo ", RolloID)
#----------------------GPIO Steuerung------------------------------------
def GPIOControl(RolloID, ThreadCounter):
    global UpdateAvalible
    while True :

        for element in GPIOData:
            if(element[0] == RolloID):
                now = float(element[3])
                target= float(element[4])
                GPIO_Down = element[2]
                GPIO_Up = element[1]
                timeout = 0
                GPIO.setup(int(GPIO_Down), GPIO.OUT)
                GPIO.setup(int(GPIO_Up), GPIO.OUT)
                GPIO.output(int(GPIO_Down), GPIO.HIGH)
                GPIO.output(int(GPIO_Up), GPIO.HIGH)
                move = ""
                if(now < target):
                    timeout = float((target - now))
                    move = "Up"
                if(now > target):
                    timeout = float((now - target))
                    move = "Down"
                while(UpdateAvalible[ThreadCounter][0] == False):
                    if(timeout != 0.00 and move != ""):
                        if(move == "Up"):
                            print ("GPIO Status of Pin" + GPIO_Down + ": OFF")
                            GPIO.output(int(GPIO_Down), GPIO.HIGH)
                            print ("GPIO Status of Pin" + GPIO_Up + ": ON")
                            GPIO.output(int(GPIO_Up), GPIO.LOW)
                            if(timeout < 1):
                                time.sleep(timeout)
                                print("Movingtime: ", timeout)
                                timeout = 0
                            else:
                                print("Movingtime: ", timeout)
                                timeout = timeout - 1
                                time.sleep(1)
                        if(move == "Down"):
                            print ("GPIO Status of Pin" + GPIO_Up + ": OFF")
                            GPIO.output(int(GPIO_Up), GPIO.HIGH)
                            print ("GPIO Status of Pin" + GPIO_Down + ": ON")
                            GPIO.output(int(GPIO_Down), GPIO.LOW)
                            if(timeout < 1):
                                time.sleep(timeout)
                                print("Movingtime: ", timeout)
                                timeout = 0
                            else:
                                print("Movingtime: ", timeout)
                                timeout = timeout - 1
                                time.sleep(1)
                    elif(timeout == 0.00 and move == "Up"):
                            print ("GPIO Status of Pin"  + GPIO_Up + ": OFF")
                            GPIO.output(int(GPIO_Up), GPIO.HIGH)
                            RefreshState(RolloID, target)
                            move = ""
                    elif(timeout == 0.00 and move == "Down"):
                            print ("GPIO Status of Pin"  + GPIO_Down + ": OFF")
                            GPIO.output(int(GPIO_Down), GPIO.HIGH)
                            RefreshState(RolloID, target)
                            move =  ""
                    else:
                        time.sleep(4)
                print("Checking for updates", int(RolloID))
        UpdateAvalible[ThreadCounter][0] = False

def getGPIOData():
    try:
        data = urllib.urlopen(BaseURL + "?Call=getRolloData").read()
    except urllib.error.HTTPError as e:
        print(e.code)
        print(e.read())
    output = json.loads(data)
    AllData = []
    try:
        DeviceID = urllib.urlopen(BaseURL + "?Call=getDeviceID&IP=" + ip + "&Hostname=" + hostname ).read()
    except urllib.error.HTTPError as e:
        print(e.code)
        print(e.read())
    ThreadCounter = 0
    for element in output:
        if(element['Device_ID'] == DeviceID):
            AllData.append([element['Rollo_ID'], element['Rollo_GPIO_UP'], element['Rollo_GPIO_DOWN'], element['Rollo_state_now'], element['Rollo_state_target'], element['Rollo_moving_time'], ThreadCounter])
            ThreadCounter = ThreadCounter + 1
    return(AllData)

#-------------------------------------------------------------------XML-RPC----------------------------------------------------------------------------------------------------------------------
def UpdateData():
    global GPIOData
    time.sleep(1)
    GPIOData = getGPIOData()
    global UpdateAvalible
    for element in UpdateAvalible:
        element[0] = True

def GPIOStatusChange():
    print("New data available")
    t = Thread(target=UpdateData)
    t.start()
    return str

def checkConnection():
        try:
            data = urllib.urlopen(BaseURL, timeout=10)
            return True
        except urllib.error.HTTPError as e:
            print(e.code)
            print(e.read())
            return False

def on_subscribe(client, userdata, mid, granted_qos):
    print("Subscribed: "+str(mid)+" "+str(granted_qos))

def on_message(client, userdata, msg):
    if(str(msg.payload) == "Update"):
        GPIOStatusChange()
        print(msg.topic+" "+str(msg.qos)+" "+str(msg.payload))

def on_disconnect(client, userdata, rc):
    if rc != 0:
        print "Unexpected MQTT disconnection. Will auto-reconnect"

def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))
    client.subscribe("Rollo", qos=1)

if __name__ == '__main__':
    while(checkConnection == False):
        print("Connection Error !")
        time.sleep(10)
    GPIOData = getGPIOData()
    for element in GPIOData:
        UpdateAvalible.append([False])
        print("Shutter Number " + element[0] +" registed")
        t = Thread(target=GPIOControl, args=(element[0], element[6]))
        #element[3], element[4], element[1], element[2]
        t.setName(element[0])
        t.setDaemon(True)
        t.start()

    try:
            client = paho.Client()
            client.username_pw_set("web", "123456")
            client.on_connect = on_connect
            client.on_subscribe = on_subscribe
            client.on_message = on_message
            client.connect("172.31.1.205", 1883)
            client.on_disconnect = on_disconnect
            client.loop_forever()


    except (KeyboardInterrupt, SystemExit):
            # Not strictly necessary if daemonic mode is enabled but should be done if possible
            GPIO.cleanup()
            print(" bye bye !")


#-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
