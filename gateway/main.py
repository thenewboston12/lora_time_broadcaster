from network import LoRa
from network import WLAN
from network import Bluetooth
from network import Server
import struct
import socket
import pycom
import time
import utime
import gc
from machine import RTC
import machine
import struct
import ubinascii

# saving energy by disabling all the networks
bt = Bluetooth()
bt.deinit()
server = Server()
server.deinit()

#enable garbage collector
gc.enable()


pycom.heartbeat(False)
off = 0x000000
green = 0x00FF00
red = 0xFF0000
blue = 0x0000FF
white = 0xFFFAFA
orange = 0xFC9D1D
light_green = 0xdbe003
purple = 0xb134eb

# change this for appropriate WiFi access point

_WIFI_SSID = "TP-Link_56B1"
_WIFI_PASS = "34134634"

# _WIFI_SSID = "NU"
# _WIFI_PASS = "1234512345"

_NTP_URL = "pool.ntp.org"
_TIMEZONE_OFFSET = 6* 60**2 # For GMT +6

# time period to send the sync packet (in ms)
_TIME_PERIOD_MS = 5000

# set LoRa parameters
lora = LoRa(mode=LoRa.LORA, region=LoRa.EU868, bandwidth=LoRa.BW_125KHZ)

pycom.rgbled(white)

#Connect to the Wi-Fi network
wlan = WLAN(mode=WLAN.STA)
wlan.connect(ssid=_WIFI_SSID, auth=(WLAN.WPA2, _WIFI_PASS))

while not wlan.isconnected():
    pycom.rgbled(orange)
    machine.idle()
print("connected to WiFi")

pycom.rgbled(blue)


_PREFIX = lora.mac()[7]
_LORA_PKG_FORMAT = "!bi"


# Connect to ntp server
rtc = machine.RTC()

rtc.ntp_sync(_NTP_URL, 20)

while not rtc.synced():
    pycom.rgbled(orange)
    machine.idle()

pycom.rgbled(purple)

# set timzeone offset
time.timezone(_TIMEZONE_OFFSET)

# create a socket
s = socket.socket(socket.AF_LORA, socket.SOCK_RAW)
s.setblocking(False)



while True:
    pycom.rgbled(green)

    cur_time = time.localtime()
    print("\nCurrent time: ", cur_time)

    # get precise time
    seconds = time.time() +1
    seconds = int(seconds)

    pkg = struct.pack(_LORA_PKG_FORMAT, _PREFIX, seconds)

    # send 1 byte + seconds
    s.send(pkg)

    # Print some stats
    print("Time On Air:", lora.stats()[7], "ms")

    print("RSSI:", lora.stats()[1])

    print("SNR:", lora.stats()[2])


    pycom.rgbled(off)

    # Send sync time every _TIME_PERIOD_MS milliseconds
    time.sleep_ms(_TIME_PERIOD_MS)

print("THE END")
