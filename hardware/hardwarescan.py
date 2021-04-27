'''
Created on Apr. 25, 2021

@author: Pete Harris

Designed to be a standalone script that gets implemented as a Linux service.

cd /lib/systemd/system
sudo nano beercadia-hardware-scan.service
------------
[Unit]
Description=Python script to scan and report values from the hardware
After=multi-user.target

[Service]
Type=simple
ExecStart=/usr/bin/python3 /home/pi/Beercadia/hardware/hardwarescan.py
Restart=on-abort
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
------------
sudo chmod 644 /lib/systemd/system/beercadia-hardware-scan.service
chmod +x /home/pi/Beercadia/hardware/hardwarescan.py
sudo systemctl daemon-reload
sudo systemctl enable beercadia-hardware-scan.service
sudo systemctl start beercadia-hardware-scan.service

'''

import logging
import logging.handlers
import sys
import os.path
import time
import sqlite3
import paho.mqtt.client as mqtt
import Adafruit_DHT

class HardwareScanner():
    """
    
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
    
    Note that the Logging module can't use f-strings, so we have to use %s formatting instead.
    """
    DATABASENAME = "Beercadia.db"
    MOSQUITTO_BROKER = "127.0.0.1"
    MOSQUITTO_PORT = 1883   # default
    CORE_LOOP_SLEEP = 2
    
    @staticmethod
    def mqtt_on_publish(client, userdata, messageid):
        logger.debug("MQTT client published messageID [%s]", messageid)
    
    @staticmethod
    def mqtt_on_connect(client, userdata, flags, returncode):
        print("inside mqtt_on_connect; unsure why this isn't getting called")
        failcodes = {
            0: "Connection successful",
            1: "Connection refused - incorrect protocol version",
            2: 'Connection refused - invalid client identifier',
            3: "Connection refused - server unavailable",
            4: "Connection refused - bad username or password",
            5: "Connection refused - not authorised"
        }
        if returncode == 0:
            logger.debug("MQTT client connected OK.")
        elif returncode < 6:
            logger.debug("MQTT client failed: %s.", failcodes[returncode])
        else:
            logger.debug("MQTT client failed: unknown code [%s]", returncode)
    
    @staticmethod
    def mqtt_on_disconnect(client, userdata, returncode):
        if returncode == 0:
            logger.debug("MQTT client disconnected safely")
        else:
            logger.debug("MQTT client disconnected [code %s]", returncode)
    
    
    def __init__(self, thermosleep=360, thermoretry=15, db=None):
        self.thermosleep = thermosleep
        self.thermo_retry = thermoretry
        self.db = db if db else os.path.join(os.path.dirname(os.path.realpath(__file__)), "..", HardwareScanner.DATABASENAME)
        self.validateDB()
        self.mosquitto_client = mqtt.Client("Beercadia_hardware_scanner")
        self.mosquitto_client.on_publish = HardwareScanner.mqtt_on_publish
        self.mosquitto_client.on_connect = HardwareScanner.mqtt_on_connect
        self.mosquitto_client.on_disconnect = HardwareScanner.mqtt_on_disconnect
        
        self.hardware = {
            "Chamber/Thermometer": { "sleep": 0, "sensor": Adafruit_DHT.DHT22, "pin": 4 }
        }
    
    def scan(self):
        while True:
            self.hardwareReadInLoop("Chamber/Thermometer")
            
            time.sleep(HardwareScanner.CORE_LOOP_SLEEP)
        # end scan
    
    def hardwareReadInLoop(self, hardwarekey):
        if hardwarekey not in self.hardware:
            return False
        
        myretry = 10
        mysleep = 30
        mytype = "???"
        if "Thermometer" in hardwarekey:
            myretry = self.thermo_retry
            mysleep = self.thermosleep
            mytype = "thermometer"
        
        self.hardware[hardwarekey]["sleep"] -= 1
        if self.hardware[hardwarekey]["sleep"] < (-1 - myretry):
            logger.warning("Warning: Failed to read %s %s times in a row.", mytype, myretry)
            self.hardware[hardwarekey] = -1
        if self.hardware[hardwarekey]["sleep"] < 0:
            if mytype == "thermometer":
                humidity, temperature = self._DHT_reader(self.hardware[hardwarekey]["sensor"], self.hardware[hardwarekey]["pin"])
                if humidity is not None and temperature is not None:
                    logger.info("Hardware read: %s: Temperature: %.1f°C, Humidity: %.1f%%", hardwarekey, temperature, humidity)
                    mqttkey = "Beercadia/" + hardwarekey.rpartition("/")[0] + "/"
                    self.update( [(mqttkey+"Temperature", temperature), (mqttkey+"Humidity", humidity)] )
                    self.hardware[hardwarekey]["sleep"] = int( mysleep / HardwareScanner.CORE_LOOP_SLEEP )
        return True
    
    def update(self, items):
        """
        Update the shared database (for web access), then post to Mosquitto.
        """
        self.publish(items)
        self.updateDB(items)
        return
    
    def publish(self, items):
        self.mosquitto_client.connect(HardwareScanner.MOSQUITTO_BROKER, HardwareScanner.MOSQUITTO_PORT)
        for key, val in items:
            returncode, messageid = self.mosquitto_client.publish(key, val, retain=True)
            logger.info("%s = %s [ID:%s]", key, val, messageid)
        self.mosquitto_client.disconnect()
        return
        
    def updateDB(self, items):
        try:
            conn = sqlite3.connect(self.db)
            c = conn.cursor()
            for key, val in items:
                c.execute("INSERT OR REPLACE INTO Hardware (Key, Value) VALUES (?, ?)", (key, val))
            conn.commit()
            conn.close()
            logger.debug("INSERT OR REPLACE INTO Hardware (Key, Value) VALUES (%s, %s) succeeded", key, val)
        except Exception as e:
            if conn:
                conn.rollback()
                conn.close()
            logger.error("Failed to write to database %s ERROR: %s", self.db, str(e))
        return
    
    def validateDB(self):
        try:
            conn = sqlite3.connect(self.db)
            c = conn.cursor()
            c.execute("CREATE TABLE IF NOT EXISTS Hardware (Key TEXT PRIMARY KEY, Value REAL)")
            conn.commit()
            conn.close()
            logger.debug("CREATE TABLE IF NOT EXISTS Hardware (Key TEXT PRIMARY KEY, Value REAL) succeeded")
        except Exception as e:
            if conn:
                conn.rollback()
                conn.close()
            logger.error("Failed to validate/create table Hardware in database %s ERROR: %s", self.db, str(e))
        return
    
    
    def _DHT_reader(self, sensor, pin):
        """
        Returns humidity, temperature
        """
        return Adafruit_DHT.read(sensor, pin)



if __name__ == '__main__':
    """ stdout logging should appear in journalctl when this is run as a service """
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    rotatingLogHandler = logging.handlers.RotatingFileHandler(os.path.join(os.path.dirname(os.path.realpath(__file__)), "hardwarescan.log"), maxBytes=65536, backupCount=2)
    rotatingLogHandler.setLevel(logging.INFO)
    rotatingLogHandler.setFormatter(logging.Formatter(fmt="%(asctime)s %(levelname)s: %(message)s", datefmt="%Y/%m/%d %H:%M:%S"))
    logger.addHandler(rotatingLogHandler)
    stdoutLogHandler = logging.StreamHandler(sys.stdout)
    stdoutLogHandler.setLevel(logging.WARNING)
    stdoutLogHandler.setFormatter(logging.Formatter(fmt="%(asctime)s %(levelname)s: %(message)s", datefmt="%Y/%m/%d %H:%M:%S"))
    logger.addHandler(stdoutLogHandler)
    
    obj = HardwareScanner(thermosleep=60)
    obj.scan()
