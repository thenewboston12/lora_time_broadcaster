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
green = 0x00FF00
red = 0xFF0000
off = 0x000000

# define timezone offset
_TIMEZONE_OFFSET = 6 * 60 * 60
# define the period in which time information comes from the gateway in ms
_TIME_PERIOD_MS = 10000

lora = LoRa(mode=LoRa.LORA, region=LoRa.EU868)

s = socket.socket(socket.AF_LORA, socket.SOCK_RAW)
s.setblocking(False)

# set timezone offset
time.timezone(_TIMEZONE_OFFSET)

# LoRa.ALWAYS_ON  --- the radio is always listening for incoming - packets whenever a transmission is not taking place
# LoRa.TX_ONLY --- the radio goes to sleep as soon as the transmission completes
# LoRa.SLEEP  --- the radio is sent to sleep permanently and won’t accept any commands until the power mode is changed.

lora.power_mode(LoRa.ALWAYS_ON)

synced = False

print("listening...")
chrono = Timer.Chrono()


chrono2 = Timer.Chrono()


chronoSleep = Timer.Chrono()

chronoLoop = Timer.Chrono()

wakeup_chrono = Timer.Chrono()

while True:


    # Turn on the radio module to listen for incoming sync packet
    # lora.power_mode(LoRa.ALWAYS_ON)

    if synced:
        print("\n---IN SYNC---")
        lora.power_mode(LoRa.ALWAYS_ON)
        wakeup_chrono.reset()
        wakeup_chrono.start()


        print("from unsynced: it tooK: ", chrono2.read_ms())

        print("1 loop took: ", chronoLoop.read_ms())
        chronoLoop.reset()
        chronoLoop.start()

        chrono.reset()
        chrono.start()

        print(str(wakeup_chrono.read_ms())+"ms since waking up the radio")
        buf = s.recv(64)

        while chrono.read_ms() < 300 and len(buf) < 1:
            buf = s.recv(64)

        print("That loop ran for: ", chronoLoop.read_ms())
        chrono.stop()

        if len(buf) < 1:
            print("MISSED!")
            synced = False
            pycom.rgbled(off)

        elif len(buf) >1 and len(buf) < 5:

            seconds = int.from_bytes(buf, 'little', False)

            out = time.localtime(seconds)

            print("{}.{}.{} {}:{}:{}".format(out[2],out[1],out[0],out[3],out[4],out[5]))

            pycom.rgbled(green)

            # Turn off the receiver (radio module)
            # lora.power_mode(LoRa.SLEEP)


            print("before sleep: ", chronoLoop.read_ms())
            lora.power_mode(LoRa.SLEEP)

            time.sleep_ms(4950)

            chronoSleep.reset()
            chronoSleep.start()

            # time_to_sleep = _TIME_PERIOD_MS -3
            # time.sleep_ms(time_to_sleep)
        else :
            synced = False
            pycom.rgbled(off)

            print("buffer length mismatch ")

    # If not synced
    else:
        print("unsynced:(")
        buf  = s.recv(512)
        if len(buf) >1 and len(buf) < 5:
            chrono2.reset()
            chrono2.start()

            seconds = int.from_bytes(buf, 'little', False)

            out = time.localtime(seconds)

            print("\n{}.{}.{} {}:{}:{}\n".format(out[2],out[1],out[0],out[3],out[4],out[5]))

            synced = True

            pycom.rgbled(green)

            #  turn off the receiver radio module

            # sleep until the next time period
            # time_to_sleep = _TIME_PERIOD_MS -3
            # time.sleep_ms(time_to_sleep)


            lora.power_mode(LoRa.SLEEP)
            time.sleep_ms(4500)

            lora.power_mode(LoRa.ALWAYS_ON)

        else:
            time.sleep_ms(500)


# 0.00020 -> 0.2 ms
# 0.6 ms

print("THE END!")

