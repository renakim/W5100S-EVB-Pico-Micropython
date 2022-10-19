import utime
from machine import Pin, SPI
import network
import json
import random

from umqtt.simple import MQTTClient

# Certificate path
cert_file = 'cert/device_certification.crt.der'
key_file = 'cert/privateKey.key.der'

device_id = '<Device Id>'
hostname = '<Hostname or Endpoint>'
mqtt_topic = f'$aws/things/{device_id}/shadow/update'

global client


# W5x00 init
def init_ethernet():
    spi = SPI(0, 2_000_000, mosi=Pin(19), miso=Pin(16), sck=Pin(18))
    nic = network.WIZNET5K(spi, Pin(17), Pin(20))   # spi, cs, reset pin
    # nic.ifconfig(('192.168.1.20','255.255.255.0','192.168.1.1','8.8.8.8'))
    # Using DHCP
    nic.active(True)
    while not nic.isconnected():
        utime.sleep(1)
        # print(nic.regs())
        print('Connecting ethernet...')

    print(f'Ethernet connected. IP: {nic.ifconfig()}')


# Init MQTT client
def init_mqtt_client():
    global client
    try:
        # Get certificates
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
        print("Connecting to MQTT server...")
        client.connect()
        print(f"MQTT Client Connected to {client.server}")
    except Exception as e:
        print(f'init_mqtt_client error: {e}')


def main():
    # Init network
    init_ethernet()

    # Init MQTT Client
    init_mqtt_client()

    def callback_handler(topic, message_receive):
        print(f"Received message: {message_receive}")

    try:
        global client

        # Subscribe
        client.set_callback(callback_handler)
        client.subscribe(topic=mqtt_topic)

        # Publish
        for i in range(0, 10):
            # Get random values
            temperature = random.uniform(20, 30)
            humidity = random.uniform(40, 50)
            data = {
                "temperature": temperature,
                "humidity": humidity
            }
            # data = {'message': f'Message from W5100S-EVB-Pico ({i})'}

            msg = json.dumps(data)
            print(f"Sending telemetry: {msg}")
            client.publish(topic=mqtt_topic, msg=msg)
            utime.sleep(5)
    except Exception as e:
        print(e)

    # # Send a C2D message and wait for it to arrive at the device
    # print("waiting for message")
    # client.wait_msg()


if __name__ == "__main__":
    main()
