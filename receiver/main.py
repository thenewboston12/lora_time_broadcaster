from network import LoRa
from network import Bluetooth
from network import Server
import socket
import time
import pycom
import struct
from machine import Timer

# Turn off unnecessary modules to conserve energy
bt = Bluetooth()
bt.deinit()
server = Server()
server.deinit()

pycom.heartbeat(False)

# colors
green = 0x00FF00
red = 0xFF0000
off = 0x000000

# define timezone offset
TIMEZONE_OFFSET = 6 * 60 * 60

# define the period in which time information comes from the gateway in ms
TIME_PERIOD_MS = 5000
GUARD_TIME = 750


# Initialize the LoRa radio module
# SF = 12
lora = LoRa(mode=LoRa.LORA, region=LoRa.EU868,  bandwidth=LoRa.BW_125KHZ,  sf=12)

s = socket.socket(socket.AF_LORA, socket.SOCK_RAW)
s.setblocking(False)

# set timezone offset
time.timezone(TIMEZONE_OFFSET)

synced = False

print("listening...")

chrono        = Timer.Chrono()
wakeup_chrono = Timer.Chrono()
chrono2       = Timer.Chrono()
chrono3       = Timer.Chrono()
chronoProcess = Timer.Chrono()

while True:
    if synced:
        print("\n---IN SYNC---")

        # turn on the radio module
        wakeup_chrono.reset()
        wakeup_chrono.start()
        lora.power_mode(LoRa.ALWAYS_ON)
        # print(str(wakeup_chrono.read_ms())+"ms since waking up the radio")

        loop_t = chrono3.read_ms()
        print("1 loop took", str(loop_t), "ms")
        chrono3.reset()
        chrono3.start()

        buf = ''
        chrono.reset()
        chrono.start()
        # while chrono.read_ms() < 1500 and len(buf) < 1:
        #     buf = s.recv(32)
        # wait_time = chrono.read_ms()

        print(str(chrono2.read_ms())+"ms since first receive")
        chrono2.reset()

        try:
            s.setblocking(True)
            s.settimeout(2)
            buf = s.recv(32)
            while (True):
                buf  = s.recv(32)
                if(len(buf)> 1):
                    print("success")
                    break

        except:
            print("socket timeout ")

        print("receiver waited for " + str(chrono.read_ms()) + "ms")
        chrono.stop()

        chronoProcess.reset()
        chronoProcess.start()


        # if missed the sync timing then packet length will be 0
        # and receiver is out of sync
        if len(buf) < 1:
            print("MISSED!")
            synced = False
            pycom.rgbled(off)

        # right size for the incoming integer
        elif len(buf) >1:
            seconds = int.from_bytes(buf, 'little', False)
            out = time.localtime(seconds)
            print("Time: {}.{}.{} {}:{}:{}".format(out[2],out[1],out[0],out[3],out[4],out[5]))
            pycom.rgbled(green)

            # Turn off the receiver (radio module)
            lora.power_mode(LoRa.SLEEP)

            # if loop_time < 1000 and big_loop >40:
            #     GUARD_TIME -= 30
            GUARD_TIME  = 500
            t = TIME_PERIOD_MS - GUARD_TIME

            # print("b4 sleep: " + str(chronoProcess.read_ms())+"ms")
            time.sleep_ms(t)
        else :
            # unexpected case when we got a large packet
            synced = False
            pycom.rgbled(off)
            print("buffer length mismatch ")

    # If not synced ###########################################################
    else:
        print("---OUT OF SYNC---")
        s.setblocking(True)
        buf  = s.recv(32)
        # s.setblocking(False)

        if len(buf) >1 and len(buf) < 5:
            chrono2.reset()
            chrono2.start()
            seconds = int.from_bytes(buf, 'little', False)

            out = time.localtime(seconds)

            print("\n{}.{}.{} {}:{}:{}\n".format(out[2],out[1],out[0],out[3],out[4],out[5]))

            synced = True

            pycom.rgbled(green)

            #  turn off the receiver radio module
            lora.power_mode(LoRa.SLEEP)

            # wait until the next time period
            t = TIME_PERIOD_MS - 1000
            time.sleep_ms(t)

        else:
            time.sleep_ms(50)
