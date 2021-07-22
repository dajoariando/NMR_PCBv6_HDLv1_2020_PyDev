"""
MQTT node for receiving pulse sequence commands from host node

Created: 22 July 2021
Updated:
Verification:

Authors: Ittai Baum
"""

import time
import paho.mqtt.client as paho
import json
import os
import sys
from nmr_t2_auto import nmr_t2_auto

base_dir = os.path.dirname( os.path.dirname( os.path.abspath( __file__ ) ) )
sys.path.append( base_dir )



# define callback
def on_message_RF( client, userdata, msg ):
    global totaltime

    data_decode = str( msg.payload.decode( "utf-8", "ignore" ) )
    # print("data Received type", type(data_decode))
    print( "data Received", data_decode )
    # print("Converting from Json to Object")
    data = json.loads( data_decode )  # decode json data
    # cpmg settings
    if(data['turn_off']==0):
        cpmg_freq = data['cpmg_freq']
        pulse1_us = data['pulse1_us']  # 75 for Cheng's coil. pulse pi/2 length.
        pulse2_us = data['pulse2_us']  # pulse pi length
        echo_spacing_us = data['echo_spacing_us']  # 200
        scan_spacing_us = data['scan_spacing_us']
        samples_per_echo = data['samples_per_echo']  # 3072
        echoes_per_scan = data['echoes_per_scan']  # 20
        init_adc_delay_compensation = data['init_adc_delay_compensation']  # acquisition shift microseconds.
        number_of_iteration = data['number_of_iteration']  # number of averaging
        ph_cycl_en = data['ph_cycl_en']
        dconv_lpf_ord = data['dconv_lpf_ord']  # downconversion order
        dconv_lpf_cutoff_Hz = data['dconv_lpf_cutoff_Hz']  # downconversion lpf cutoff
        client_data_folder = data['client_data_folder']
        nmr_t2_auto( cpmg_freq, pulse1_us, pulse2_us, echo_spacing_us, scan_spacing_us, samples_per_echo, echoes_per_scan, init_adc_delay_compensation, number_of_iteration, ph_cycl_en, dconv_lpf_ord, dconv_lpf_cutoff_Hz, client_data_folder )
        
        dataout = {'done' : 1}
        
        client.publish("HeadImager/RF_Coil",json.dumps(dataout))
        
        print('CPMG Complete')
    else:
        print('Turn Off')
        client_RF.disconnect()  # disconnect
        client_RF.loop_stop()  # stop loop
        #exit()
        #quit()
        #sys.exit()
        os._exit(0)
        print('Exit?')
# Apply Sequence
    # Returns voltages read from each pulse
    
    #data_MMU = {'Time': time.time(),
         #'ModuleID':ModuleID,
         #'DataOut': DataOut.tolist()}

    #data_MMU_out = json.dumps( data_MMU )

    #client.publish( "HeadImager/RF_Coil", data_MMU_out )  # publish

    #totaltime.append( data_in["Time"] )


broker = "broker.hivemq.com"

totaltime = []

client_RF = paho.Client( "RF Coil")

# bind function to callback #
client_RF.on_message = on_message_RF
############################

# connect MMU
print( "connecting to broker ", broker )
client_RF.connect( broker )  # connect MMU
client_RF.loop_start()  # start loop to process received messages
print( "subscribing to", broker )
client_RF.subscribe( "HeadImager/Host/RF_Coil/Instructions" )  # subscribe

turn_off = 0;

try:
    while(1):
        #print('Checking')
        time.sleep( 1000 )

except KeyboardInterrupt:
    client_RF.disconnect()
    client_RF.loop_stop()

client_RF.disconnect()  # disconnect
client_RF.loop_stop()  # stop loop
