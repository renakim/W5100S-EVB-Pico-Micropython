import utime
import time
from machine import Pin, SPI
import network
import json
import random
from binascii import a2b_base64, b2a_base64

from hmacSha256 import HMACSha256
from umqtt.robust import MQTTClient
from util import init_logger

CONNECTION_STRING = "<Your Device Connection String>"

DELIMITER = ";"
VALUE_SEPARATOR = "="


def parse_connection(connection_string):
    cs_args = connection_string.split(DELIMITER)
    dictionary = dict(arg.split(VALUE_SEPARATOR, 1) for arg in cs_args)
    return dictionary


def get_current_time():
    t = time.localtime()
    # Tuple: (year, month, mday, hour, minute, second, weekday, yearday)
    timestr = f'{t[0]:02d}-{t[1]:02d}-{t[2]:02d}T{t[3]:02d}:{t[4]:02d}:{t[5]:02d}'
    return timestr


def newPrint(msg):
    print(f'[{get_current_time()}] {msg}')


global client

# Parse the connection string into constituent parts
dict_keys = parse_connection(CONNECTION_STRING)
hostname = dict_keys.get("HostName")
device_id = dict_keys.get("DeviceId")
private_key = dict_keys.get("SharedAccessKey")

# Create username following the below format '<HOSTNAME>/<DEVICE_ID>'
username = hostname + '/' + device_id

# Azure IoT Hub Topics
telemetry_topic = f"devices/{device_id}/messages/events/"
c2d_topic = f"devices/{device_id}/messages/devicebound/#"


logger = init_logger('azure_main')


# W5x00 init
def w5x00_init():
    spi = SPI(0, 2_000_000, mosi=Pin(19), miso=Pin(16), sck=Pin(18))
    nic = network.WIZNET5K(spi, Pin(17), Pin(20))   # spi, cs, reset pin
    # nic.ifconfig(('192.168.1.20','255.255.255.0','192.168.1.1','8.8.8.8'))
    # Using DHCP
    nic.active(True)
    nic.ifconfig('dhcp')
    while not nic.isconnected():
        utime.sleep(1)
        newPrint(nic.regs())

    newPrint(f'IP info: {nic.ifconfig()}')


def init_mqtt_client(sas_token_str):
    global client
    try:
        client = MQTTClient(
            client_id=device_id,
            server=hostname,
            user=username,
            password=sas_token_str,
            port=8883,
            # ssl_params={"key": key, "cert": cert},
            keepalive=3600,
            ssl=True
        )
        newPrint("Connecting to MQTT server...")
        client.connect()
        newPrint(f"MQTT Client Connected to {client.server}")

    except Exception as e:
        newPrint(f'init_mqtt_client error: {e}')


def generate_device_sas_token(uri, key, expiry):
    def _quote(s):
        r = ''
        for c in str(s):
            if (c >= 'a' and c <= 'z') or (c >= '0' and c <= '9') or (c >= 'A' and c <= 'Z') or (c in '.-_'):
                r += c
            else:
                r += '%%%02X' % ord(c)
        return r

    ttl = int(utime.time()) + expiry
    uri = _quote(hostname + "/devices/" + device_id)
    sign_key = uri + "\n" + str(ttl)
    key = a2b_base64(key)
    hmac = HMACSha256(key, sign_key)
    signature = _quote(b2a_base64(hmac).decode().strip())

    token = f'sr={uri}&sig={signature}&se={ttl}'

    return 'SharedAccessSignature ' + token


def main():
    # Init ethernet
    w5x00_init()

    # Get SAS Token
    sas_token_str = generate_device_sas_token(hostname, private_key, 3600)  # 1h
    # newPrint(sas_token_str)
    # newPrint(device_id, hostname, username)

    # Init MQTT client
    init_mqtt_client(sas_token_str)

    client.reconnect()
    newPrint('client reconnect..')

    def callback_handler(topic, message_receive):
        newPrint("Received message")
        newPrint(message_receive)

    client.set_callback(callback_handler)
    client.subscribe(topic=c2d_topic)
    newPrint('client subscribe start..')

    # Send telemetry
    repeat = 1000
    for i in range(0, repeat):
        temperature = random.uniform(20, 30)
        humidity = random.uniform(40, 50)
        data = {
            "temperature": temperature,
            "humidity": humidity
        }
        msg = json.dumps(data)
        newPrint(f"Sending telemetry: [{i}/{repeat}]{msg}")
        client.publish(topic=telemetry_topic, msg=msg)
        utime.sleep(3)

    # Send a C2D message and wait for it to arrive at the device
    # newPrint("waiting for message")
    # client.wait_msg()


if __name__ == "__main__":
    main()
