
---
This README is an edit from the original documents below.
* https://github.com/Azure-Samples/IoTMQTTSample/blob/master/src/MicroPython/readme.md
* 
---


# Connect to Azure IoT Hub Using MQTT with Micropython on W5100S-EVB-Pico

## 


## Getting started with Micropython
See [this page](https://docs.micropython.org/en/latest/esp32/tutorial/intro.html) to install the ESP toolchain and Micropython on your ESP32.


## Using MQTT

All samples have been coded using MQTT as protocol.
Micropython uses 2 MQTT libraries :- `umqtt.simple` and `umqtt.robust`. 
The samples have been tried using both of these mqtt libraries.
Each sample has 2 functionalities :-
* Telemetry to IoT Hub
* Receive Message from IoT Hub

First check if `umqtt` is already installed by doing `help('modules')` on the ESP 32 board. If umqtt is there you may not need the below 2 libraries.

```python
import upip
upip.install('micropython-umqtt.robust')
```
You also need to grab its dependency, micropython-umqtt.simple:
`upip.install('micropython-umqtt.simple')`

Currently the sample uses `umqtt robust` but the same sample can be written with `umqtt simple`

The code will tehn create a connection and call reconnect (in robust library, only reconnect is available)
```python
## Create UMQTT ROBUST or UMQTT SIMPLE CLIENT
mqtt_client = create_mqtt_client(client_id=device_id, hostname=hostname, username=username, password=sas_token_str, port=8883, keepalive=120, ssl=True)

print("connecting")
mqtt_client.reconnect()
```

You then be able to subscribe to MQTT topic
```python
subscribe_topic = get_c2d_topic(device_id)
mqtt_client.set_callback(callback_handler)
mqtt_client.subscribe(topic=subscribe_topic)
```

Sending the message is just a call:
```python
mqtt_client.publish(topic=topic, msg=messages[i])
```
Same waiting for a cloud to device message is just:
```python
## Send a C2D message and wait for it to arrive at the device
print("waiting for message")
mqtt_client.wait_msg()
```

## Possible Errors
In case of the following errors while trying to make a connection do the following things :-

- `MQTTException: 5` : Check password used for connection
- `List index out of range` : Check wifi connection parameters
