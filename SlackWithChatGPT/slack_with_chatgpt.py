# Author: Rena Kim

from machine import Pin, SPI
import network
import utime
import urequests
import gc

import json
import time
import ujson


"""
Variables
"""
# OpenAI API Key
OPENAI_API_KEY = "<OpenAI API Key>"
OPENAI_ENDPOINT = "https://api.openai.com/v1/chat/completions"

# Slack API URL
SLACK_API_URL = "https://slack.com/api/chat.postMessage"
# Slack API Token
SLACK_API_TOKEN = "<Slack API Token>"


def get_date():
    t = time.localtime()
    timestr = f'{t[0]:02d}-{t[1]:02d}-{t[2]:02d}'
    return timestr


def get_current_time():
    t = time.localtime()
    # Tuple: (year, month, mday, hour, minute, second, weekday, yearday)
    timestr = f'{t[0]:02d}-{t[1]:02d}-{t[2]:02d}T{t[3]:02d}:{t[4]:02d}:{t[5]:02d}'
    return timestr


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


# ! Testing ChatGPT Prompt.. Not completed.
english_msg_for_slack = "I want you to be an English teacher who helps a study for every time for me(korean). I'll send a message every time with Slack. Make 2 intermediate-level English words, their explanations, and 3 example sentences. Please include a word of encouragement at the end. Write the explanations and example sentences in Korean and English both. Add the appropriate emoji in front of the word so it's visible at a glance. Please set the format as a 'blocks' value for Slack API with markdown list and set the title 'word' and sub-titles are [meaning, example sentence]. Finally, wrap the 'blocks value' with code block. Do not use the variable name. ## RETURN ONLY THE CODE BLOCK. REMOVE PRE-TEXT AND POST-TEXT."


def has_korean(text):
    for c in text:
        # if ord(c) > 128:
        if u'\uAC00' <= c <= u'\uD7A3':
            return True
    return False


def gpt_main(subject, message):
    headers = {"Authorization": f"Bearer {OPENAI_API_KEY}", "Content-Type": "application/json; charset=utf-8"}
    data = {
        "model": "gpt-3.5-turbo",
        "messages": [
            {"role": "system", "content": "You are a my English teacher with Slack API."},
            {"role": "user", "content": message}
        ]
    }

    response = urequests.post(OPENAI_ENDPOINT, headers=headers, data=json.dumps(data))
    if response.status_code == 200:
        response_data = json.loads(response.text)
        # print('response_data:', response_data)
        body = response_data["choices"][0]["message"]["content"]
        # print(body)
        print(f'Response body:\n {body}')

        new_body = body
        if 'blocks=' in body:
            print('==> Remove blocks=')
            new_body = body.replace('blocks=', '').strip()
        elif 'blocks = ' in body:
            print('==> Remove blocks = ')
            new_body = body.replace('blocks = ', '').strip()

        if '```' in body:
            print('==> Split by ```')
            templist = body.split('```')
            print(f'templist: {templist}')
            for i in range(len(templist)):
                if 'section' in templist[i]:
                    new_body = templist[i].strip()
                    break
        else:
            new_body = body

        # print(f'New body: {new_body}')
        blocks = new_body

        try:
            jsonbody = json.loads(new_body)
            print(f'jsonbody type: {type(jsonbody)}')

            if type(jsonbody) == dict:
                blocks = jsonbody['blocks']
            elif type(jsonbody) == list:
                blocks = jsonbody
            else:
                print('Wrong response.')
        except Exception as e:
            print(f'Block error: {e}')

        try:
            # Message to send slack
            message = {
                "channel": "#daily-english",
                "text": subject,
                "blocks": blocks
            }

            headers = {
                "Authorization": f"Bearer {SLACK_API_TOKEN}"
            }

            if has_korean(json.dumps(blocks)):
                print('Has korean')
                headers["Content-Type"] = "application/json; charset=utf-8"
            else:
                print('Not has korean')
                headers["Content-Type"] = "application/json"

            body_data = ujson.dumps(message).encode('utf-8')
            print(f'body_data: {body_data}')
            resp = urequests.post(
                SLACK_API_URL,
                headers=headers,
                # json=message
                data=body_data
            )

            print(f'Slack response text: {resp.text}')
            result = json.loads(resp.text)
            if (result["ok"]):
                print(">> Slack message sent successfully.")
            else:
                print(">> Slack message sent failed.")
        except Exception as e:
            print(e)

    else:
        print(f"Error: {response.text}")


def main():
    # Init ethernet
    init_ethernet()

    while True:
        # Get the current time
        # current_hour = time.localtime()[3]
        current_minute = time.localtime()[4]

        if current_minute == 0:
            english_subject = f"[{get_current_time()}] It's time to study!"
            gpt_main(english_subject, f"{english_msg_for_slack}")
            print(f'time: {get_current_time()}')

        time.sleep(60)


main()
