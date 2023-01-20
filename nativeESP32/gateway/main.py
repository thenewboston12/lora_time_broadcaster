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

oled_lines("Time Syncrhonization", "and Broadcaster", " ", " ")

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
_TIME_PERIOD_MS = 5000

# set LoRa parameters
lora.set_spreading_factor(12)
lora.set_frequency(433.1)

#Connect to the Wi-Fi network
wlan = network.WLAN(network.STA_IF)
wlan.active(True)
if not wlan.isconnected():
    print('connecting to network...')
    wlan.connect(_WIFI_SSID, _WIFI_PASS)
    while not wlan.isconnected():
        pass
print("connected to WiFi")
oled_lines("Time Syncrhonization", "and Broadcaster", "Connected to WiFi", " ")

_LORA_TIME_FORMAT = "!I"
_LORA_PREFIX_FORMAT = "!b"

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
        set_time()

        oled_lines("Time Syncrhonization", "and Broadcaster", "Set NTP clock", " ")
        time.sleep(30)

_thread.start_new_thread(ntp_sync, ())
time.sleep(5)

while True:
    cur_time = time.localtime()
    print("\nCurrent time: ", cur_time)

    # get precise time
    seconds = time.time() + 1

    time_pkg = struct.pack(_LORA_TIME_FORMAT, seconds)

    # send time packet
    led.value(1)
    lora.send(time_pkg)
    print("Sent time packet")
    led.value(0)

    # Send sync time every _TIME_PERIOD_MS milliseconds
    time.sleep_ms(_TIME_PERIOD_MS)
