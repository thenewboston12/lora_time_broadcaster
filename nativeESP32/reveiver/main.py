import socket
import struct
import network
import binascii
import ubinascii
import time
import uos
import _thread
import uerrno
import sys
from machine import SoftI2C, Pin, SPI, reset, idle, RTC
from lora import LoRa
import ssd1306
from time import sleep
import utime
from chrono import Chrono


led = Pin(25,Pin.OUT) # Heltec V2
# led = Pin(2,Pin.OUT) # TTGO
rst = Pin(16, Pin.OUT)
rst.value(1)
scl = Pin(15, Pin.OUT, Pin.PULL_UP)
sda = Pin(4, Pin.OUT, Pin.PULL_UP)
i2c = SoftI2C(scl=scl, sda=sda, freq=450000)
oled = ssd1306.SSD1306_I2C(128, 64, i2c, addr=0x3c)
oled.poweron()

def oled_lines(line1, line2, line3, line4):
    oled.fill(0)
    oled.text(line1, 0, 0)
    oled.text(line2, 0, 10)
    oled.text(line3, 0, 25)
    oled.text(line4, 0, 35)
    oled.show()

oled_lines("Time Sync", "and Broadcaster", "RECEIVER", " ")

# SPI pins
SCK  = 5
MOSI = 27
MISO = 19
CS   = 18
RX   = 26

spi = SPI(
    1,
    baudrate=1000000,
    sck=Pin(SCK, Pin.OUT, Pin.PULL_DOWN),
    mosi=Pin(MOSI, Pin.OUT, Pin.PULL_UP),
    miso=Pin(MISO, Pin.IN, Pin.PULL_UP),
)
spi.init()

lora = LoRa( spi, cs=Pin(CS, Pin.OUT), rx=Pin(RX, Pin.IN), )

# time period to send the sync packet (in ms)
_TIME_PERIOD_MS = 10_000
_AIRTIME_MS = 1320
_GUARD_TIME_MS = 30

# set LoRa parameters
lora.set_spreading_factor(12)
lora.set_frequency(433.1)

_LORA_TIME_FORMAT = "!HII"
_LORA_PREFIX_FORMAT = "!b"

rtc = RTC()

chrono = Chrono()
c2 = Chrono()
need_time = 1
xtime = 0
timeout = 800_000
synced = 0

netid =0
digest =0

def s_handler(recv_pkg):
    global xtime
    # print(recv_pkg)
    if (len(recv_pkg) > 2):
        try:
            (netid, xtime, digest ) = struct.unpack(_LORA_TIME_FORMAT, recv_pkg)
            print("NETID: ", netid)
            print("XTIME: ", xtime)
            print("DIGEST: ", digest)

            #TODO: check the digest on the message 
        except:
            print("Could not unpack!")
        if (xtime > 0):
            print("Got sync time!", xtime)

unsync = False
c2.start()
while(True):
    chrono.reset()
    chrono.start()
    oled_lines("Time Sync", "RECEIVER", "Waiting for sync...", " ")
    print("Waiting for sync/time...")
    xtime = 0
    sync_start = chrono.read_us()
    led.value(1)
    lora.on_recv(s_handler)
    lora.recv()
    while(chrono.read_us() - sync_start < _AIRTIME_MS*1000) and (synced == 1):
        if (xtime > 0):
            print("caught while idle")
            break

    print("synced:", synced)
    print("xtime:",  xtime)
    while(True) and (synced == 0):
        if (xtime > 0):
            synced = 1
            break

    print("1 LOOP in ms: ", c2.read_us()/1000)
    c2.reset()
    c2.start()

    led.value(0)
    # failed to get the packet
    if (xtime == 0):
        print("OUT OF SYNC!")
        synced = 0

    if (need_time == 1):
        out = time.localtime(xtime)
        print("{}.{}.{} {}:{}:{}".format(out[2],out[1],out[0],out[3],out[4],out[5]))
    lora.sleep()
    _SLEEP_TIME_MS = _AIRTIME_MS -500
    time.sleep_us(_TIME_PERIOD_MS*1000 -_SLEEP_TIME_MS*1000 )
    print("--------")
