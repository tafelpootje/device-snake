import serial
import sys
import sqlite3 as lite

from Adafruit_CharLCD import Adafruit_CharLCD
from subprocess import *
from time import sleep, strftime
from datetime import datetime

ser = serial.Serial('/dev/ttyAMA0', 2400, timeout=1)
lcd = Adafruit_CharLCD()
lcd.begin(16, 1)

whatToExpect = 0
deviceID = 0
userID = 0
previousScan = 0
curTag = 0
lcdMessage = "Hello"


con = None
cur = None
	
def databaseQueryOne(query, arguments):
	con = lite.connect('www/devicelab/data/devicelabdb')
	cur = con.cursor()    
	cur.execute(query, arguments)
	result = cur.fetchone()
	con.commit()
	con.close()
	return result
def databaseQueryAll(query, arguments):
	con = lite.connect('www/devicelab/data/devicelabdb')
	cur = con.cursor()    
	cur.execute(query, arguments)
	result = cur.fetchall()
	con.commit()
	con.close()
	return result
	

def scanCanBeAny(rfid):
	global whatToExpect
	global lcdMessage
	global userID
	global deviceID
	data = databaseQueryOne("SELECT count(*) FROM device WHERE ID = ?", [rfid])
	if data[0] == 0:
		data = databaseQueryAll("SELECT * FROM users WHERE ID = ?", [rfid])
		if len(data)==0:
			databaseQueryOne("INSERT OR REPLACE INTO failures VALUES (?, ?)",[rfid, datetime.now()])
			LCDPrint("This tag is added to 'Failures' contact an admin")
			whatToExpect = 0
			lcdMessage = "Please scan your id or a device"
		else:
			whatToExpect = 2
			userID=rfid
			lcdMessage = "Please scan the device you need"
	else:
		print 4
		whatToExpect = 1
		deviceID=rfid
		lcdMessage = "Please scan id to return device"
	tag = 0
	print 12

def scanShouldBeUser (rfid):
	global whatToExpect
	global lcdMessage
	global userID
	global deviceID
	print 5
	data = databaseQueryOne("SELECT count(*) FROM users WHERE ID = ?", [rfid,])
	print 'deviceID = ' + deviceID
	if data[0]==0:
		print 6
		LCDPrint("This is not a known user tag, contact an admin")
		whatToExpect = 0
	else:
		print 7
		data = databaseQueryOne("SELECT users_id FROM leases WHERE devices_id = ?",[deviceID])
		if (data is None) or (len(data) == 0):
			print 8
			databaseQueryOne("DELETE FROM leases WHERE devices_id = ? AND users_id = ?",[deviceID, rfid])
			LCDPrint("The device is back, thank you.")
			whatToExpect = 0
		else:
			print 9
			data = databaseQueryOne("SELECT users.firstname FROM users,leases WHERE leases.devices_id == ? AND users.id == leases.users_id",[deviceID])
			LCDPrint("This device was not from you " + data[1])
	tag = 0

def scanShouldBeDevice (rfid):
	global whatToExpect
	global lcdMessage
	global userID
	global deviceID
	data = databaseQueryOne("SELECT count(*) FROM device WHERE ID = ?", [rfid,])
	if data[0]==0:
		LCDPrint("This is not a known device tag, contact an admin")
		sleep(1)
	else:
		data = databaseQueryOne("SELECT users_id FROM leases WHERE devices_id = ?",[rfid])
		if (data is None) or (len(data) == 0):
			databaseQueryOne("insert or replace INTO leases VALUES(?,?,?)",[rfid, userID, datetime.now()])
			LCDPrint("HAPPY TESTING!")
			sleep(1)
		else:
			data = databaseQueryOne("SELECT firstname FROM users WHERE id = ?",[data[1]])
			LCDPrint("This device should be in the hands of " + data[1])
			sleep(1)
	tag = 0
	whatToExpect = 0
	lcdMessage = "Please scan your id or a device"


def LCDPrint(data):
	if data:
		lcd.clear()
		if len(data) > 32:
			scroll(data)
		else:
			lcd.message(data[:16])
			lcd.message('\n')
			lcd.message(data[16:])

def scroll(data):
	while (len(data) > 30):
		lcd.clear()
		lcd.message(data[:16])
		lcd.message('\n')
		lcd.message(data[16:32])
		sleep(1)
		scroll(data[2:])
		break

lcdMessage = "Please scan your id or a device"
while True:
	tag = ser.read(12)
	print "whatToExpect"
	print whatToExpect
	if (len(tag) == 0):
		LCDPrint(lcdMessage)
		continue
	elif (ord(tag[0]) == 0x0A) and (ord(tag[11]) == 0x0D) and (previousScan != tag[1:11]):
		previousScan = tag
		curTag = tag[1:11] #exclude start x0A and stop x0D bytes
		print tag
		LCDPrint("Thank you ")
		if whatToExpect == 0:
			scanCanBeAny(curTag)
		elif whatToExpect == 1:
			scanShouldBeUser(curTag)
		else:
			scanShouldBeDevice(curTag)
		#whatToExpect = nextValues[0]
		#lcdMessage = nextValues[1]
		LCDPrint('Remove tag from reader!')
		while len(tag) !=0:
			tag = ser.read(1)
		sleep(1)
