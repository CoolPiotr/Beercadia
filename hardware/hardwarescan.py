'''
Created on Apr. 25, 2021

@author: Pete Harris
'''

import time
import sqlite3
import paho.mqtt.client as mqtt
import Adafruit_DHT

class HardwareScanner():
    """
    DHT_SENSOR_CHAMBER = Adafruit_DHT.AM2302
    DHT_PIN_CHAMBER = 7
    
    Database keys should also be the same as Mosquitto message URLs; i.e. slash delimited.
    This is the list of categories:
                                        #
    Beercadia/                          # The overall machine
        Ambient/                        # Stuff external to the machine; local barometric pressure, ambient temperature, etc.
            Pressure/                   # Barometric pressure, just because I still have a sensor for that. Can tell altitude.
            Altitude/                   # Calculated altitude from pressure.
        Chamber/                        # The main refrigeration chamber. Generic, not tied to the keg(s).
            Temperature/                #
            Humidity/                   # Don't really care about humidity, but it comes with the DHT22 temperature sensor.
        LeftKeg/                        # The keg on the left.
            Weight/                     # Weight of the left keg sensor, in kilograms.
            Temperature/                # Temperature of magnetically fastened thermometer.
            Name/                       # The name of the beer (entered via web, not provided by sensor)
        RightKeg/                       # The keg on the right.
            Weight/                     # Weight of the right keg sensor, in kilograms.
            Temperature                 #
            Name/
        Gas/                            # Gas cannister info. Could be made into left/right if we put two on the machine.
            Weight/                     # Weight of the gas cannister, in kilograms.
    
    """
    DATABASE = "../Beercadia.db"
    MOSQUITTO_BROKER = "127.0.0.1"
    MOSQUITTO_PORT = 1883   # default
    
    
    def __init__(self, sleep=5, db=None):
        self.sleep = sleep
        self.db = db if db else HardwareScanner.DATABASE
        self.validateDB()
        self.mosquitto_client = mqtt.Client("hardwarescanner")
    
    def scan(self):
        while True:
            #humidity, temperature = self.DHT_reader(Adafruit_DHT.DHT22, 4)
            humidity, temperature = self.getChamberTemperature()
            if humidity is not None and temperature is not None:
                print(f"Temperature: {temperature:0.1f}°C, Humidity: {humidity:0.1f}%")
                self.update( [("Beercadia/Chamber/Humidity", humidity), ("Beercadia/Chamber/Temperature", temperature)] )
            
            time.sleep(self.sleep)
        # end scan
    
    def update(self, items):
        """
        Update the shared database (for web access), then post to Mosquitto.
        """
        self.publish(items)
        self.updateDB(items)
        return
    
    def publish(self, items):
        for key, val in items:
            self.mosquitto_client.publish(key, val)
        return
        
    def updateDB(self, items):
        conn = sqlite3.connect(self.db)
        c = conn.cursor()
        for key, val in items:
            c.execute("INSERT OR REPLACE INTO Hardware (Key, Value) VALUES (?, ?)", (key, val))
        conn.commit()
        conn.close()
        return
    
    def validateDB(self):
        conn = sqlite3.connect(self.db)
        c = conn.cursor()
        c.execute("CREATE TABLE IF NOT EXISTS Hardware (Key TEXT PRIMARY KEY, Value REAL)")
        conn.commit()
        conn.close()
        return
    
    def getChamberTemperature(self):
        """
        """
        return self._DHT_reader(Adafruit_DHT.DHT22, 4)
    
    def _DHT_reader(self, sensor, pin):
        """
        Returns humidity, temperature
        """
        return Adafruit_DHT.read(sensor, pin)
        # return fake sample values until tested from Raspberry Pi
        #return 0.65, 22.1 


if __name__ == '__main__':
    obj = HardwareScanner()
    obj.scan()
