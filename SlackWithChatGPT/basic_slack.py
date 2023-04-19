from machine import Pin, SPI
import network
import utime
import urequests
import ujson

# Slack API Token
SLACK_API_TOKEN = "<Slack API Token>"
# Slack API URL
SLACK_API_URL = "https://slack.com/api/chat.postMessage"


# W5x00 init
def init_ethernet():
    spi = SPI(0, 2_000_000, mosi=Pin(19), miso=Pin(16), sck=Pin(18))
    nic = network.WIZNET5K(spi, Pin(17), Pin(20))   # spi, cs, reset pin
    # Using DHCP
    nic.active(True)
    while not nic.isconnected():
        utime.sleep(1)
        # print(nic.regs())
        print('Connecting ethernet...')

    print(f'Ethernet connected. IP: {nic.ifconfig()}')


def main():
    init_ethernet()

    # Message to send
    message = {
        "channel": "#general",
        "text": "Hello, World!"
    }

    # Repeat message every 30 seconds
    # while True:
    for i in range(0, 1):
        # Send message using Slack API

        response = urequests.post(
            SLACK_API_URL,
            headers={
                "Authorization": "Bearer " + SLACK_API_TOKEN,
                "Content-type": "application/json"
            },
            # json=message
            data=ujson.dumps(message)
        )

        # Print response
        print(response.json())

        # Wait for seconds before sending the message again
        utime.sleep(30)


main()
