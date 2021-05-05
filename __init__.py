'''
Required Raspberry Pi setup
---------------------------
sudo apt update
sudo apt upgrade -y
sudo apt install mosquitto -y
sudo systemctl enable mosquitto
sudo apt install sqlite3
sudo apt install python3-pip

Required Python modules
=======================
sudo pip3 install paho-mqtt
sudo pip3 install Adafruit_DHT

Required for web deployment on NGINX and uWSGI
..............................................
sudo apt install nginx -y
sudo pip3 install flask uwsgi
(see article https://www.raspberrypi-spy.co.uk/2018/12/running-flask-under-nginx-raspberry-pi/)

'''