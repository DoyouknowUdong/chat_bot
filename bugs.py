# -*- coding: utf-8 -*-
import json
import os
import re
import urllib.request

from bs4 import BeautifulSoup
from slackclient import SlackClient
from flask import Flask, request, make_response, render_template

app = Flask(__name__)

slack_token = "xoxb-507364314564-508936047190-dTcO1Q4ubNpa2b4WAElBLP7F"
slack_client_id = "507364314564.507365584964"
slack_client_secret = "0b2a3b06b001673f303f7617202f70e1"
slack_verification = "Ym42nf8NRTiDpYiiGkgoLOth"
sc = SlackClient(slack_token)

# 크롤링 함수 구현하기
def _crawl_naver_keywords(text):
    
    #여기에 함수를 구현해봅시다.
    #url = re.search(r'(https?://\S+)',text.split("|")[0]).group(0)
    url = 'https://music.bugs.co.kr/chart'
    req = urllib.request.Request(url)
    
    sourcecode = urllib.request.urlopen(url).read()
    soup = BeautifulSoup(sourcecode, "html.parser")
    
    s1=soup.find_all("p",class_='title')[:10]
    s2=soup.find_all("p",class_='artist')[:10]
    
    key_titles=[each.get_text().strip() for each in s1][:10]
    key_artists=[each.get_text().strip() for each in s2][:10]
    keywords=[str(i+1)+"위 : "+key_titles[i]+" / "+key_artists[i] for i in range(len(key_titles))]
    #print(keywords)
    # 한글 지원을 위해 앞에 unicode u를 붙힙니다. 
    return u'Bugs 실시간 음악 차트 Top 10\n\n'+'\n'.join(keywords)




# 이벤트 핸들하는 함수
def _event_handler(event_type, slack_event):
    print(slack_event["event"])

    if event_type == "app_mention":
        channel = slack_event["event"]["channel"]
        text = slack_event["event"]["text"]

        keywords = _crawl_naver_keywords(text)
        sc.api_call(
            "chat.postMessage",
            channel=channel,
            text=keywords
        )

        return make_response("App mention message has been sent", 200,)

    # ============= Event Type Not Found! ============= #
    # If the event_type does not have a handler
    message = "You have not added an event handler for the %s" % event_type
    # Return a helpful error message
    return make_response(message, 200, {"X-Slack-No-Retry": 1})

@app.route("/listening", methods=["GET", "POST"])
def hears():
    slack_event = json.loads(request.data)

    if "challenge" in slack_event:
        return make_response(slack_event["challenge"], 200, {"content_type":
                                                             "application/json"
                                                            })

    if slack_verification != slack_event.get("token"):
        message = "Invalid Slack verification token: %s" % (slack_event["token"])
        make_response(message, 403, {"X-Slack-No-Retry": 1})
    
    if "event" in slack_event:
        event_type = slack_event["event"]["type"]
        return _event_handler(event_type, slack_event)

    # If our bot hears things that are not events we've subscribed to,
    # send a quirky but helpful error response
    return make_response("[NO EVENT IN SLACK REQUEST] These are not the droids\
                         you're looking for.", 404, {"X-Slack-No-Retry": 1})

@app.route("/", methods=["GET"])
def index():
    return "<h1>Server is ready.</h1>"

if __name__ == '__main__':
    app.run('127.0.0.1', port=8080)
