#!/usr/bin/python
import time
from flask import Flask
import MySQLdb
import serial
import datetime
import RPi.GPIO as GPIO
import wiringpi
#------------------------------------------------------------------
#------------------------------------------------------------------
# Kolejność wysyłania danych
pres= 0
damp = 1
temp = 2
light1 = 3
light2 = 4
dist = 5

# Połączenia z baza danych
db=MySQLdb.connect(host='localhost', user='piecia', passwd='piecia1', db='home')
c=db.cursor()

ser = serial.Serial('/dev/ttyACM0',9600)
prev_day = datetime.datetime.now()
while 1:
    buf = list(map(float,ser.readline().split()))
    now = datetime.datetime.now()
    formatted_date = now.strftime('%Y-%m-%d %H:%M:%S')
    c.execute('INSERT INTO sensors VALUES(%s,%s,%s,%s,%s,%s,%s)', (buf[pres], buf[damp], buf[temp], buf[light1], buf[light2], buf[dist], formatted_date))
    db.commit()


