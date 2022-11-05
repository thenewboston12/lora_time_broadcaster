# lora_time_broadcaster (Using Spreading Factor 12) Guard times are still too long
## gateway 
LoRa gateway that transmits the NTP time at regular intervals defined by `_TIME_PERIOD_MS` currently set to 5 seconds
Also, the WiFi credentials need to be altered by changing `WIFI_SSID` and `_WIFI_PASS` variables

 
## receiver
Receives the time synchronization packets in `4 byte` integers, at a regular interval defined by `_TIME_PERIOD_MS` parameter.
Also prints out the time that it took for the radio module to wake up and be ready to receive packets.
