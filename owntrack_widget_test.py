#!/bin/env python2

import paho.mqtt.client as mqtt
import time
import random
import string
import curses
import textwrap

baseTopic = "owntracks/tst2/paho"

baseX = 48
baseY = 11
numWayps = 5
wayps = {}

def id_generator(size=6, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))

for i in range(numWayps):
    wayX = (50 - random.randint(1, 100)) / float(50) + baseX
    wayY = (50 - random.randint(1, 100)) / float(50) + baseY
    wayps[id_generator(4)] = (wayX, wayY)

#print 'Generated waypoints ' + str(wayps)

# The callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, flags, rc):
    print("Connected with result code " + str(rc))

# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg):
    #print(msg.topic+" "+str(msg.payload))
    #print "-> Received - " + msg.topic + ': ' + msg.payload
    if msg.topic == baseTopic + '/cmd':
        send_waypoints(client)

def send_waypoints(client):
    waypsStr = ''
    comma = ''
    for w, v in wayps.iteritems():
        waypsStr = waypsStr + comma + '''
{ "_type": "waypoint",
            "tst": %d,
            "lat": %f,
            "lon": %f,
            "rad": %d,
            "desc": "%s" }
''' % (int(time.time()), v[0], v[1], 200, w)
        comma = ','
    waypsStr = '''
{ "_type": "waypoints",
    "waypoints": [
''' + waypsStr + '] }'
    wtopic = baseTopic + '/waypoint'
    #print '<- Publishing - ' + wtopic + ': ' + waypsStr
    client.publish(wtopic, payload=waypsStr, retain=False)

client = mqtt.Client()
client.on_connect = on_connect

client.username_pw_set("tst2", "test")
client.connect("m21.cloudmqtt.com", 17744, 60)
client.subscribe('owntracks/#')

send_waypoints(client)

roamStep = 800

def main_loop(stdscr, client, baseTopic, baseX, baseY, roamStep, wayps):
    def loc_fill(s):
        return textwrap.fill(s, (stdscr.getmaxyx()[1] - 5))

    cornerX = baseX - 2; cornerY = baseY - 1
    
    randX = (50 - random.randint(1, 100)) / float(100) + baseX
    randY = (50 - random.randint(1, 100)) / float(100) + baseY
    stdscr.addstr(0, 0, "Seed " + str(randX) + "," + str(randY))
    stdscr.addstr(1, 0, loc_fill("Waypoints: " + str(wayps)))

    client.on_message = lambda client, userdata, msg: stdscr.addstr(42, loc_fill("-> Received - " + msg.topic + ": " + msg.payload)); stdscr.refresh()

    tmpY = 20
    stdscr.addstr(tmpY-1, 2, 'B @' + str(cornerX) + ',' + str(cornerY))
    for w, v in wayps.iteritems():
        wX = int((v[0] - cornerX) * 25)
        wY = int((v[1] - cornerY) * 15)
        stdscr.addstr(wY, wX, w)
        stdscr.addstr(tmpY, 2, "W " + w + "@" + str(wX) + ',' + str(wY))
        tmpY += 1
    stdscr.refresh()
    
    while True:
        msg = ('{"_type":"location","acc":2,"batt":100,"lat":' + str(randX) + ',"lon":' + str(randY) + ',"tid":"tst2","tst":'
               + str(int(time.time())) + '}')
        stopic = baseTopic
        client.publish(stopic, payload=msg, qos=0, retain=False)
        stdscr.addstr(40, 0, loc_fill("<- Sent - " + stopic + ': ' + msg))
        
        stdscr.addstr(45, 0, "Press q to quit, hjklr to move location")
        stdscr.refresh()
        c = stdscr.getkey()
        offX = 0; offY = 0
        if c == 'q':
            break
        elif c == 'r':
            offX = (50 - random.randint(1, 100))
            offY = (50 - random.randint(1, 100))
        elif c == 'h':
            offX = -10;
        elif c == 'l':
            offX = 10;
        elif c == 'j':
            offY = -10;
        elif c == 'k':
            offY = 10
        randX += offX / float(roamStep)
        randY += offY / float(roamStep)
        
        wX = int((randX - cornerX) * 25)
        wY = int((randY - cornerY) * 15)
        stdscr.addstr(wY, wX, '+')
        stdscr.addstr(tmpY, 2, "P " + w + "@" + str(wX) + ',' + str(wY))

curses.wrapper(main_loop, client, baseTopic, baseX, baseY, roamStep, wayps)
