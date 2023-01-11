from network import LoRa
from network import Bluetooth
from network import Server
import socket
import time
import pycom
import struct
from machine import Timer
import struct

# Turn off unnecessary modules to conserve energy
bt = Bluetooth()
bt.deinit()
server = Server()
server.deinit()


pycom.heartbeat(False)
green = 0x00FF00
red = 0xFF0000
off = 0x000000

# define timezone offset
_TIMEZONE_OFFSET = 6 * 60 * 60
# define the period in which time information comes from the gateway in ms
_TIME_PERIOD_MS = 5000
_LORA_TIME_FORMAT = "!i"
_LORA_PREFIX_FORMAT = "!B"


lora = LoRa(mode=LoRa.LORA, region=LoRa.EU868)

s = socket.socket(socket.AF_LORA, socket.SOCK_RAW)
s.setblocking(False)

# set timezone offset
time.timezone(_TIMEZONE_OFFSET)


synced = False

print("listening...")
chrono = Timer.Chrono()
wakeup_chrono = Timer.Chrono()
need_time = False


while True:
    if synced:
        print("\n---IN SYNC---")
        # used for timing
        wakeup_chrono.reset()
        wakeup_chrono.start()

        # turn on the radio module
        lora.power_mode(LoRa.ALWAYS_ON)
        print(str(wakeup_chrono.read_ms())+"ms since waking up the radio module")
        buf = s.recv(64)

        chrono.reset()
        chrono.start()
        # wait for 300ms for the incoming sync packet
        # it waits 300ms initially then 50ms
        while chrono.read_ms() < 300 and len(buf) < 1:
            buf = s.recv(64)
        chrono.stop()

        # if missed the sync timing then packet length will be 0
        # and receiver is out of sync

        # received a sync packet
        # 83 is ascii for 'S'
        if (len(buf) > 0) and (buf[0] == 83):
            print("SYNC: Received a sync packet")

            prefix = struct.unpack(_LORA_PREFIX_FORMAT, buf)

            print("SYNC: prefix ", chr(prefix[0]))

            pycom.rgbled(green)

            # Turn off the receiver (radio module)
            lora.power_mode(LoRa.SLEEP)

            # 50ms is enough to wake up the radio and receive the sync signal
            time_to_sleep = _TIME_PERIOD_MS -50
            time.sleep_ms(time_to_sleep)

        # Received a time packet
        elif need_time and (len(buf) > 2) and len(buf) <5:
            print("SYNC: Received a time pakcet")
            seconds = struct.unpack(_LORA_TIME_FORMAT, buf)

            out = time.localtime(seconds[0])

            print("{}.{}.{} {}:{}:{}".format(out[2],out[1],out[0],out[3],out[4],out[5]))

            pycom.rgbled(green)

            # Turn off the receiver (radio module)
            lora.power_mode(LoRa.SLEEP)

            # 50ms is enough to wake up the radio and receive the sync signal
            time_to_sleep = _TIME_PERIOD_MS -50
            time.sleep_ms(time_to_sleep)
        else :
            # unexpected case when we got a large packet
            print("MISSED!")
            synced = False
            pycom.rgbled(off)


    # If not synced
    else:
        print("OUT OF SYNC")
        buf  = s.recv(512)

        # received a sync packet
        # 83 is ascii for 'S'
        if (len(buf) > 0) and (buf[0] == 83):
            print("ASYNC: Received a sync packet")

            prefix = struct.unpack(_LORA_PREFIX_FORMAT, buf)

            print("ASYNC: prefix ", chr(prefix[0]))


            synced = True

            pycom.rgbled(green)

            # Turn off the receiver (radio module)
            lora.power_mode(LoRa.SLEEP)

            # wait until the next time period
            # needs to wake up earlier(500ms) to get the receiver ready()
            time_to_sleep = _TIME_PERIOD_MS -500
            time.sleep_ms(time_to_sleep)

        # Received a time packet
        elif need_time and (len(buf) > 2) and len(buf) <5:
            print("ASYNC: Received a time pakcet")
            seconds = struct.unpack(_LORA_TIME_FORMAT, buf)

            out = time.localtime(seconds)

            print("{}.{}.{} {}:{}:{}".format(out[2],out[1],out[0],out[3],out[4],out[5]))
            synced = True

            pycom.rgbled(green)

            # Turn off the receiver (radio module)
            lora.power_mode(LoRa.SLEEP)

            # wait until the next time period
            # needs to wake up earlier(500ms) to get the receiver ready()
            time_to_sleep = _TIME_PERIOD_MS -500
            time.sleep_ms(time_to_sleep)

        else:
            # packet did not come yet
            time.sleep_ms(500)
