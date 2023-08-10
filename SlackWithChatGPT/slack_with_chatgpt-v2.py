# Author: Rena Kim

from machine import Pin, SPI, ADC
import network
import utime
import urequests

import json
import time
import ujson

# import neopixel
import dht
# from picobricks import SSD1306_I2C


"""
Variables
"""
# OpenAI API Key
OPENAI_API_KEY = "<OpenAI API Key>"
OPENAI_ENDPOINT = "https://api.openai.com/v1/chat/completions"

# Slack API URL and token
SLACK_API_TOKEN = "<Slack API Token>"
SLACK_API_URL = "https://slack.com/api/chat.postMessage"

NEWS_API_KEY = "<News API Key>"


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


def has_korean(text):
    for c in text:
        # if ord(c) > 128:
        if u'\uAC00' <= c <= u'\uD7A3':
            return True
    return False


def get_news_list(api_key):
    url = f"https://newsapi.org/v2/top-headlines?country=us&apiKey={api_key}&category=technology&pageSize=3&page={time.localtime()[3]}"
    print(f'url: {url}')
    response = urequests.get(url, headers={"User-Agent": "DevApp/1.0"})
    # print(f'response: {response}')

    if response.status_code == 200:
        data = json.loads(response.text)

        print(f'News data: {data}')

        if data["status"] == "ok":
            news_articles = data["articles"]
            news_list = [f"News {i + 1}) [{article['title']}]({article['url']})" for i, article in enumerate(news_articles)]
            # print(f'news_list: {news_list}')
            return news_list
        else:
            print("News request failed.")
            return None
    else:
        print(f'Error: {response.status_code}, {response.text}')
        return None


def main():
    # Init sensors
    dht11 = dht.DHT11(Pin(11))
    ldr = ADC(Pin(27))

    # Init ethernet
    init_ethernet()

    while True:
        # Get the current time
        current_hour = time.localtime()[3]
        current_minute = time.localtime()[4]

        if current_minute == 0 or current_minute == 30:
            subject = f"[{get_current_time()}] Let's start good day!"

            # Get news list
            news_list = get_news_list(NEWS_API_KEY)
            news_str = ', '.join(news_list)

            dht11.measure()
            user_text = f'Temperature: {dht11.temperature()}, Humidity: {dht11.humidity()}, Light: {ldr.read_u16()}, {news_str}'
            # print(f'user_text: {user_text}, {json.dumps(user_text)}')

            system_text = "As my manager, you provide helpful information as body text for the day. Use the following step-by-step instructions to respond to user inputs. Step 1 - The user provides data for 3 sensor values for office. Create today's news based on sensor data. Includes today's news from user input. Step 2 - Make 2 intermediate-level English words, their explanations, and 3 example sentences. Step 3 - Write a quote of the day and finish the article. Step 4 - Combine and format the Step 1~3 all information (office sensor values, 2 English words, News, Quote) as a 'blocks' value with code block for Slack API. Do not use the code block name.   ## RETURN ONLY THE CODE BLOCK. REMOVE PRE-TEXT AND POST-TEXT. DO NOT INCLUDE CODE BLOCK TYPE."

            headers = {"Authorization": f"Bearer {OPENAI_API_KEY}", "Content-Type": "application/json; charset=utf-8"}
            data = {
                "model": "gpt-3.5-turbo",
                "messages": [
                    {"role": "system", "content": system_text},
                    {"role": "user", "content": user_text}
                ]
            }

            # print(f'CHECK data: {json.dumps(data)}')

            response = urequests.post(OPENAI_ENDPOINT, headers=headers, data=json.dumps(data))
            if response.status_code == 200:
                response_data = json.loads(response.text)
                # print('response_data:', response_data)
                body = response_data["choices"][0]["message"]["content"]
                # print(body)
                print(f'Response body:\n {body}')

                # Remove unnecessary text
                new_body = body
                if '```python' in body:
                    print('Remove python in ```python')
                    new_body = new_body.replace('```python', '```')
                elif '```blocks' in body:
                    print('Remove blocks in ```blocks')
                    new_body = new_body.replace('```blocks', '```')

                if 'blocks=' in body:
                    print('==> Remove blocks=')
                    new_body = body.replace('blocks=', '').strip()
                elif 'blocks = ' in body:
                    print('==> Remove blocks = ')
                    new_body = body.replace('blocks = ', '').strip()

                if '```' in new_body:
                    print('Split by ```')
                    templist = new_body.split('```')
                    print(f'templist: {templist}')
                    for i in range(len(templist)):
                        if 'section' in templist[i]:
                            new_body = templist[i].strip()
                            break
                else:
                    new_body = body

                print(f'New body: {new_body}')
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
                        "channel": "#general",
                        "text": subject,
                        "blocks": blocks
                    }
                    headers = {"Authorization": f"Bearer {SLACK_API_TOKEN}"}
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
                        data=body_data
                    )

                    print(f'Slack response text: {resp.text}')
                    result = json.loads(resp.text)
                    if (result["ok"]):
                        print("Slack message sent successfully.")
                    else:
                        print("Slack message send failed.")
                except Exception as e:
                    print(e)

            else:
                print(f"Error: {response.text}")

        time.sleep(60)


main()
