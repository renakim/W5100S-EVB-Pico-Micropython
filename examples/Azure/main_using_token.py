import utime
from machine import Pin, SPI
import network
import json

from binascii import a2b_base64, b2a_base64
from hmacSha256 import HMACSha256

from util import create_mqtt_client, get_telemetry_topic, get_c2d_topic, parse_connection

CONNECTION_STRING = "<Your Device Connection String>"

# Parse the connection string into constituent parts
dict_keys = parse_connection(CONNECTION_STRING)
hostname = dict_keys.get("HostName")
device_id = dict_keys.get("DeviceId")
private_key = dict_keys.get("SharedAccessKey")

# Create username following the below format '<HOSTNAME>/<DEVICE_ID>'
username = hostname + '/' + device_id


# W5x00 init
def w5x00_init():
    spi = SPI(0, 2_000_000, mosi=Pin(19), miso=Pin(16), sck=Pin(18))
    nic = network.WIZNET5K(spi, Pin(17), Pin(20))   # spi, cs, reset pin
    # nic.ifconfig(('192.168.1.20','255.255.255.0','192.168.1.1','8.8.8.8'))
    # Using DHCP
    nic.active(True)
    while not nic.isconnected():
        utime.sleep(1)
        print(nic.regs())

    print(f'IP info: {nic.ifconfig()}')


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
    # Init network
    w5x00_init()

    # Create UMQTT ROBUST or UMQTT SIMPLE CLIENT
    # print(device_id, hostname, username)

    # Get SAS Token
    sas_token_str = generate_device_sas_token(hostname, private_key, 3600)  # 1h
    # print(sas_token_str)
    mqtt_client = create_mqtt_client(client_id=device_id, hostname=hostname, username=username, password=sas_token_str, port=8883, keepalive=120, ssl=True)
    print("Connecting")
    mqtt_client.reconnect()

    def callback_handler(topic, message_receive):
        print("Received message")
        print(message_receive)

    subscribe_topic = get_c2d_topic(device_id)
    mqtt_client.set_callback(callback_handler)
    mqtt_client.subscribe(topic=subscribe_topic)

    print("Publishing")
    topic = get_telemetry_topic(device_id)

    # Send telemetry
    for i in range(0, 10):
        msg = json.dumps({'message': f'Message from W5100S-EVB-Pico ({i})'})
        print(f"Sending telemetry: {msg}")
        mqtt_client.publish(topic=topic, msg=msg)
        utime.sleep(2)

    # Send a C2D message and wait for it to arrive at the device
    print("waiting for message")
    mqtt_client.wait_msg()


if __name__ == "__main__":
    main()
