'''
Created on Apr. 25, 2021

@author: Pete Harris
'''

import logging
import time
import sqlite3
import paho.mqtt.client as mqtt
import Adafruit_DHT

class HardwareScanner():
    """
    DHT_SENSOR_CHAMBER = Adafruit_DHT.DHT22
    DHT_PIN_CHAMBER = 4
    
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
            Name/                       #
        Gas/                            # Gas cannister info. Could be made into left/right if we put two on the machine.
            Weight/                     # Weight of the gas cannister, in kilograms.
    
    """
    DATABASE = "../Beercadia.db"
    MOSQUITTO_BROKER = "127.0.0.1"
    MOSQUITTO_PORT = 1883   # default
    CORE_LOOP_SLEEP = 2
    
    @staticmethod
    def mqtt_on_publish(client, userdata, messageid):
        pass
        #print("Published:", client, userdata, messageid)
    
    @staticmethod
    def mqtt_on_disconnect(client, userdata, returncode):
        logging.warning(f"MQTT client disconnected [code {returncode}]; attempting to reconnect...")
        while client.disconnected:
            client.connect(HardwareScanner.MOSQUITTO_BROKER, HardwareScanner.MOSQUITTO_PORT)
    
    
    def __init__(self, thermosleep=30, thermoretry=15, db=None):
        self.thermosleep = thermosleep
        self.thermo_retry = thermoretry
        self.db = db if db else HardwareScanner.DATABASE
        self.validateDB()
        self.mosquitto_client = mqtt.Client("Beercadia_hardware_scanner")
        self.mosquitto_client.on_publish = HardwareScanner.mqtt_on_publish
        self.mosquitto_client.on_disconnect = HardwareScanner.mqtt_on_disconnect
        
        self.hardware = {
            "Chamber/Thermometer": { "sleep": 0 }
        }
    
    def scan(self):
        self.mosquitto_client.connect(HardwareScanner.MOSQUITTO_BROKER, HardwareScanner.MOSQUITTO_PORT)
        while True:
            self.hardware["Chamber/Thermometer"]["sleep"] -= 1
            if self.hardware["Chamber/Thermometer"]["sleep"] < (-1 - self.thermo_retry):
                logging.warning(f"Warning: Failed to read thermometer {self.thermo_retry} times in a row.")
                self.hardware["Chamber/Thermometer"]["sleep"] = -1
            if self.hardware["Chamber/Thermometer"]["sleep"] < 0:
                humidity, temperature = self.getChamberTemperature()
                if humidity is not None and temperature is not None:
                    logging.info(f"Chamber: Temperature: {temperature:0.1f}°C, Humidity: {humidity:0.1f}%")
                    self.update( [("Beercadia/Chamber/Temperature", temperature), ("Beercadia/Chamber/Humidity", humidity)] )
                    self.hardware["Chamber/Thermometer"]["sleep"] = int( self.thermosleep / HardwareScanner.CORE_LOOP_SLEEP )
            
            time.sleep(HardwareScanner.CORE_LOOP_SLEEP)
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
            self.mosquitto_client.publish(key, val, retain=True)
            logging.info(f"{key} = {val}")
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
    logging.basicConfig(
        filename="hardwarescan.log", encoding="utf-8",
        format="%{asctime)s:%(levelname)s: %(message)s",
        datefmt="%Y/%m/%d %H:%M:%S",
        level=logging.INFO)
    obj = HardwareScanner(thermosleep=60)
    obj.scan()
