'''
Created on Apr. 26, 2021

@author: Pete Harris
'''

import time
import paho.mqtt.client as mqtt
import sqlite3

DATABASE = "../Beercadia.db"
MOSQUITTO_BROKER = "192.168.0.141"
MOSQUITTO_PORT = 1883   # default


def on_connect(client, userdata, flags, resultcode):
    print( "Connected.", str(resultcode) )
    # subscribe here, then it's renewed if you are reconnected.
    client.subscribe("Beercadia/#")
    
def on_message(client, userdata, message):
    print("message recieved:", str(message.topic), str(message.payload.decode("utf-8")) )
    updateDB( [(str(message.topic), str(message.payload.decode("utf-8")))] )
    print("database updated.")
    
def updateDB(items):
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    for key, val in items:
        c.execute("INSERT OR REPLACE INTO Hardware (Key, Value) VALUES (?, ?)", (key, val))
    conn.commit()
    conn.close()
    return

    
if __name__ == '__main__':
    client = mqtt.Client()
    client.on_message=on_message
    client.on_connect=on_connect
    
    client.connect(MOSQUITTO_BROKER, MOSQUITTO_PORT)
    
    client.loop_forever()