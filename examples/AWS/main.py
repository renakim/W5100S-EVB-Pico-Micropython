import utime
from machine import Pin, SPI
import network
import json
import random
import time

from umqtt.robust import MQTTClient

# Certificate path
cert_file = 'cert/certificate.crt.der'
key_file = 'cert/privateKey.key.der'

"""
Add your AWS resource information
"""
device_id = '<Device Id>'
hostname = '<Hostname or Endpoint>'

pub_topic = f'$aws/things/{device_id}/shadow/update'
sub_topic = f'$aws/things/{device_id}/shadow/accepted'

global client


def get_current_time():
    t = time.localtime()
    # Tuple: (year, month, mday, hour, minute, second, weekday, yearday)
    timestr = f'{t[0]:02d}-{t[1]:02d}-{t[2]:02d}T{t[3]:02d}:{t[4]:02d}:{t[5]:02d}'
    return timestr


def newPrint(msg):
    print(f'[{get_current_time()}] {msg}')


# W5x00 init
def init_ethernet():
    spi = SPI(0, 2_000_000, mosi=Pin(19), miso=Pin(16), sck=Pin(18))
    nic = network.WIZNET5K(spi, Pin(17), Pin(20))   # spi, cs, reset pin
    # nic.ifconfig(('192.168.1.20','255.255.255.0','192.168.1.1','8.8.8.8'))
    # Using DHCP
    nic.active(True)
    nic.ifconfig('dhcp')

    while not nic.isconnected():
        utime.sleep(1)
        # newPrint(nic.regs())
        newPrint('Connecting ethernet...')

    newPrint(f'Ethernet connected.\nIP: {nic.ifconfig()}')


# Init MQTT client
def init_mqtt_client():
    global client
    try:
        with open(key_file, "rb") as f:
            key = f.read()
        with open(cert_file, "rb") as f:
            cert = f.read()

        client = MQTTClient(
            client_id=device_id,
            server=hostname,
            port=8883,
            ssl_params={"key": key, "cert": cert},
            keepalive=3600,
            ssl=True
        )
        newPrint("Connecting to MQTT server")
        client.connect()
        newPrint(f"MQTT Client Connected to {client.server}")
        newPrint(f"Publish Topic: {pub_topic}")
    except Exception as e:
        newPrint(f'init_mqtt_client error: {e}')


def main():
    # Init network
    init_ethernet()

    # Init MQTT Client
    init_mqtt_client()

    def callback_handler(topic, message_receive):
        newPrint("Received message")
        newPrint(message_receive)

    try:
        global client

        # Subscribe
        client.set_callback(callback_handler)
        client.subscribe(topic=sub_topic)

        # Publish
        repeat = 10
        for i in range(0, repeat):
            # Get random values
            temperature = random.uniform(20, 30)
            humidity = random.uniform(40, 50)
            data = {
                "cnt": i,
                "temperature": temperature,
                "humidity": humidity
            }

            msg = json.dumps(data)
            newPrint(f"Sending telemetry: [{i+1}/{repeat}]{msg}")
            client.publish(topic=pub_topic, msg=msg)
            utime.sleep(20)

        # Send a C2D message and wait for it to arrive at the device
        newPrint(f"waiting for message.. Sub Topic: {sub_topic}")
        client.wait_msg()
    except Exception as e:
        newPrint(e)


if __name__ == "__main__":
    main()
