"""
MQTT node for receiving pulse sequence commands from host node

Created: 12 May 2021
Updated:
Verification:

Authors: Ittai Baum, Roland Probst
"""

import time
import paho.mqtt.client as paho
import json
import os
import sys

base_dir = os.path.dirname( os.path.dirname( os.path.abspath( __file__ ) ) )
sys.path.append( base_dir )

from Model.device import Device


# define callback
def on_message_MMU( client, userdata, msg ):
    global totaltime
    global ModuleID

    data_decode = str( msg.payload.decode( "utf-8", "ignore" ) )
    # print("data Received type", type(data_decode))
    print( "data Received", data_decode )
    # print("Converting from Json to Object")
    data_in = json.loads( data_decode )  # decode json data

    # select index in array corresponding to this Module
    data_in['voltage'] = data_in['voltage'][ModuleID - 1]
    data_in['currentdirection'] = data_in['currentdirection'][ModuleID - 1]

    # Apply Sequence
    # Returns voltages read from each pulse
    DataOut = device.chargedischarge( data_in )

    data_MMU = {'Time': time.time(),
         'ModuleID':ModuleID,
         'DataOut': DataOut.tolist()}

    data_MMU_out = json.dumps( data_MMU )

    client.publish( "HeadImager/ExpID_01/ModularMagnetUnits/" + str( ModuleID ), data_MMU_out )  # publish

    totaltime.append( data_in["Time"] )


# setup device drivers
device = Device()
device.initialize()
global ModuleID
ModuleID = device.device_id
print( "ModuleID:", ModuleID )

broker = "broker.hivemq.com"

totaltime = []

client_MMU = paho.Client( "Magnet" + str( ModuleID ) )

# bind function to callback #
client_MMU.on_message = on_message_MMU
############################

# connect MMU
print( "connecting to broker ", broker )
client_MMU.connect( broker )  # connect MMU
client_MMU.loop_start()  # start loop to process received messages
print( "subscribing to", broker )
client_MMU.subscribe( "HeadImager/Host/ExpID_01/Instructions" )  # subscribe

try:
    while( 1 ):
        time.sleep( 1000 )
except KeyboardInterrupt:
    client_MMU.disconnect()
    client_MMU.loop_stop()

client_MMU.disconnect()  # disconnect
client_MMU.loop_stop()  # stop loop
