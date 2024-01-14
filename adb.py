import os
import time
import settings

def screenshot( path ):
	os.system( "\"" + settings.adb_path + "\"" + " -s " + settings.device_address + " exec-out screencap -p > " + path )
	time.sleep(1)

def click(location):
	print("Adb : Tap " + str(location[0]) + " " + str(location[1]) )
	last_click_loc = location
	os.system( "\"" + settings.adb_path + "\"" + " -s " + settings.device_address + " shell input tap " + str(location[0]) + " " + str(location[1]) )
	time.sleep(3)

def swipe( from_loc, to_loc, use_time ):
	print( "Adb : Swipe from " + str(from_loc) + " to " + str(to_loc)+ " by " + str(use_time)+ " millisecond" )
	process = os.system( "\"" + settings.adb_path + "\"" + " -s " + settings.device_address + " shell input swipe "
		+ str(from_loc[0]) + " " + str(from_loc[1]) + " " + str(to_loc[0]) + " " + str(to_loc[1]) + " " + str(use_time) )
	#time.sleep(use_time/1000)
	time.sleep(2)

