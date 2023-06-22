from machine import Pin, SPI
import network
import utime
import urequests
import ujson

import json
import time
import re

OPENAI_API_KEY = "<Open AI API Key>"
OPENAI_ENDPOINT = "https://api.openai.com/v1/chat/completions"
MODEL = 'gpt-3.5-turbo'

# set Tistory API endpoint URL and access token
TISTORY_API_URL = "https://www.tistory.com/apis/post/write"
TISTORY_ACCESS_TOKEN = "<Tistory Access token>"
TISTORY_BLOG_NAME = "<Tistory blog name>"


def get_date():
    t = time.localtime()
    timestr = f'{t[0]:02d}-{t[1]:02d}-{t[2]:02d}'
    return timestr


def get_current_time():
    t = time.localtime()
    # Tuple: (year, month, mday, hour, minute, second, weekday, yearday)
    timestr = f'{t[0]:02d}-{t[1]:02d}-{t[2]:02d}T{t[3]:02d}:{t[4]:02d}:{t[5]:02d}'
    return timestr


def has_korean(text):
    for c in text:
        # if ord(c) > 128:
        if u'\uAC00' <= c <= u'\uD7A3':
            return True
    return False


user_prompt = '''
I want you to be an English learning Content Writer who helps a study for every time for people(korean). I'll post a content every time with my Blog. It uses HTML format. Provide 2 intermediate-level English words, their explanations, and comprehensive explanations and construct 3 example sentences. Concentrate on a specific aspect of English learning, such as grammar, vocabulary, or speaking skills. Deliver precise explanations, pertinent examples, and practical tips in Korean to guide and empower the learners. Write the words, explanations and example sentences in Korean and English both. Add the appropriate emoji in front of the word so it's visible at a glance. Please set the title of content include the featured 2 intermediate-level English words with HTML format in English. 
Finally, wrap the whole contents with HTML format include html, head, title tags. ## RETURN ONLY THE HTML CODE BLOCK.

Other Content: Inscribe the remaining sections of the blog post, such as introductions, conclusions, and supplementary information, in Korean while maintaining a formal tone. Integrate relevant examples, anecdotes, or personal insights in Korean to captivate the readers and establish a deeper connection with the content.

Practical Applications: Incorporate practical, real-life examples or scenarios in Korean that vividly demonstrate the application of the discussed language skills in everyday situations. This approach enables learners to grasp the significance and effectiveness of their learning journey.

Ensure that the overall tone remains formal and the writing style remains instructive throughout the blog post in Korean, fostering a professional atmosphere and providing precise guidance to the readers.
'''


def post_tistory(title, content):
    # Create Tistory API request headers
    headers = {}

    if has_korean(content):
        print('Has korean')
        headers["Content-Type"] = "application/json; charset=utf-8"
    else:
        print('Not has korean')
        headers["Content-Type"] = "application/json"

    # Create Tistory API request data
    data = {
        "access_token": TISTORY_ACCESS_TOKEN,
        "output": "json",
        "blogName": TISTORY_BLOG_NAME,
        "title": title,
        "content": content
    }
    # Send Tistory API request using urequests
    body_data = ujson.dumps(data).encode('utf-8')
    print(f'## tistory body: {body_data}')
    response = urequests.post(TISTORY_API_URL, headers=headers, data=body_data)
    # print(f'## tistory response: {response.content}')
    print(f'## tistory response: {response.content.decode("utf-8")}')


def get_title(content):
    title = None
    try:
        # Define the regex pattern to match the title tag
        pattern = r"<title>(.*?)</title>"

        # Find the match using regex
        match = re.search(pattern, content)

        # Extract the title if a match is found
        if match:
            title = match.group(1)
            print(f'title: {title}')
    except Exception as e:
        print(e)

    return title


def gpt_main():
    headers = {"Authorization": f"Bearer {OPENAI_API_KEY}", "Content-Type": "application/json"}
    data = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": "You are English Learning Content Writer for Korean."},
            {"role": "user", "content": user_prompt}
        ]
    }

    response = urequests.post(OPENAI_ENDPOINT, headers=headers, data=json.dumps(data).encode('utf-8'))
    print(f'response: {response.text}')
    if response.status_code == 200:
        print(f'response text: {response.text}')
        response_data = json.loads(response.text)
        body = response_data["choices"][0]["message"]["content"]
        print(f'body: {body}')

        title = get_title(body)
        if title is not None:
            post_tistory(title, body)


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

    while True:
        # Get the current time
        current_hour = time.localtime()[3]
        current_minute = time.localtime()[4]

        if current_minute == 0:
            gpt_main()
            print(f'time: {get_current_time()}')

        time.sleep(60)


main()
