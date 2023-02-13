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
import gc
import _thread
from chrono import Chrono
import hashlib

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

oled_lines("Time Sync", "and Broadcaster", "GATEWAY", " ")

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

#enable garbage collector
gc.enable()

_WIFI_SSID = "NU"
_WIFI_PASS = "1234512345"

_NTP_URL = "pool.ntp.org"
_TIMEZONE_OFFSET = 6*60*60 # For GMT +6

# time period to send the sync packet (in ms)
_TIME_PERIOD_MS = 10000
_AIRTIME_MS =  1320

# set LoRa parameters
lora.set_spreading_factor(12)
lora.set_frequency(433.1)

#Connect to the Wi-Fi network
wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wifi_text = _WIFI_SSID+"..."
if not wlan.isconnected():
    print('\nconnecting to',wifi_text)
    oled_lines("Time Sync", "and Broadcaster", "Connecting to", "{} ".format(wifi_text))

    wlan.connect(_WIFI_SSID, _WIFI_PASS)
    while not wlan.isconnected():
        pass
print("connected to WiFi")
oled_lines("Time Sync", "and Broadcaster", "Connected to WiFi", " ")

_LORA_TIME_FORMAT = "!HII"
_LORA_PREFIX_FORMAT = "!b"

def sha_256(message):
    hashed = binascii.hexlify(hashlib.sha256(message.encode('utf-8')).digest())
    #convert first 4 bytes to an integer
    val_int = int(hashed[:8], 16)

    return val_int


rtc = RTC()

def get_time():
    NTP_QUERY = bytearray(48)
    NTP_QUERY[0] = 0x1b
    addr = socket.getaddrinfo(_NTP_URL, 123)[0][-1]
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.settimeout(1)
    res = s.sendto(NTP_QUERY, addr)
    msg = s.recv(48)
    s.close()
    val = struct.unpack("!I", msg[40:44])[0]
    return val - 3155673600

def set_time():
    t = get_time()
    tm = utime.localtime(t+_TIMEZONE_OFFSET)
    tm = tm[0:3] + (0,) + tm[3:6] + (0,)
    rtc.datetime(tm)
    print(utime.localtime())


def ntp_sync():
    while(True):
        # Connect to ntp server
        oled_lines("Time Sync", "and Broadcaster", "Setting NTP...", " ")

        set_time()

        time.sleep(30)

_thread.start_new_thread(ntp_sync, ())
time.sleep(5)

chrono = Chrono()

chrono.start()

while True:

    cur_time = time.localtime()
    print("\nCurrent time: ", cur_time)

    # get precise time
    seconds = time.time()
    NET_ID = 33
    to_hash =str(NET_ID) + str(seconds)
    digest = sha_256(to_hash)

    time_pkg = struct.pack(_LORA_TIME_FORMAT, NET_ID, seconds, digest )


    # send time packet
    led.value(1)
    print("1 LOOP MS: ",chrono.read_us()/1000000)

    chrono.reset()
    chrono.start()

    chrono.reset()
    chrono.start()
    oled_lines("Time Sync", "and Broadcaster", "Sending Time...", " ")

    lora.send(time_pkg)
    print("Sent time packet")
    led.value(0)

    _DELAY_MS = 840
    # Send sync time every _TIME_PERIOD_MS milliseconds
    time.sleep_ms(_TIME_PERIOD_MS - _DELAY_MS)
