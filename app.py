from flask import Flask, request, abort

from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import *

#####
import requests
from bs4 import BeautifulSoup
import webbrowser

import pafy
from websocket import create_connection
import json

app = Flask(__name__)

# Channel Access Token
line_bot_api = LineBotApi('ndPIBS61LBtLU1PgA5fohOMtYFXKchqGQJYQJ2t0K6pdYoQt+ozg0kK4W3B8ubqH/lOuBDu0Kw/KZEWj9Rtt2/OEc1xatSOPmsRnwLlfugVLM2L5DWWk9YnWJ+lv6MayexWYMxb89FHX4LNGoC3ijwdB04t89/1O/w1cDnyilFU=')
# Channel Secret
handler = WebhookHandler('6d9210ca7b02dceaa9bb14fbffd84dc0')

#####
global playlist
playlist = []

def gettime(s):
    t = s.split(":")
    return int(t[0]) * 60 * 60 + int(t[1]) * 60 + int(t[2])

# 監聽所有來自 /callback 的 Post Request
@app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']
    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)
    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'

# 處理訊息
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    global playlist
    text = event.message.text.split()
    if text[0] == '!play':
        temp = ''
        for i in text[1:]:
            temp += i + ' '
        temp = temp[:-1]
        if temp.startswith('https://www.youtube.com/watch?v='):
            temp = temp
            video = pafy.new(temp)
            best = video.getbest()
            playurl = best.url
            ws = create_connection("ws://videocontrolwebsocket.herokuapp.com", http_proxy_port=80)
            ws.send(json.dumps({"type": "url", "data": playurl, 'time': gettime(video.duration), 'title': video.title}))
            print(playurl)
            ws.close()
        elif temp.startswith('https://youtu.be/'):
            temp = temp
            video = pafy.new(temp)
            best = video.getbest()
            playurl = best.url
            ws = create_connection("ws://videocontrolwebsocket.herokuapp.com", http_proxy_port=80)
            ws.send(json.dumps({"type": "url", "data": playurl, 'time': gettime(video.duration)}))
            print("Sent")
            ws.close()
        else:
            r = requests.get('https://www.youtube.com/results?search_query=' + temp)
            soup = BeautifulSoup(r.text, 'html.parser')
            select = soup.select('h3.yt-lockup-title a')
            for i in select:
                temp = 'https://www.youtube.com' + i['href']
                break
        playlist.append(temp)
        message = TextSendMessage(text = temp + ' is added to the queue.')
    elif text[0] == '!queue':
        if not playlist:
            message = TextSendMessage(text = 'The queue is empty.')
        else:
            temp = 'Now playing:\n' + playlist[0]
            if len(playlist) > 1:
                temp += '\nThe queue:\n'
                for i in playlist[1:]:
                    temp += i + '\n'
                temp = temp[:-1]
            message = TextSendMessage(text = temp)
    elif text[0] == '!nowplaying':
        message = TextSendMessage(text = 'Now playing: ' + playlist[0])
    elif text[0] == '!skip':
        if playlist:
            message = TextSendMessage(text = playlist[0] + ' is skiped.')
            playlist = playlist[1:]
        else:
            message = TextSendMessage(text = 'The queue is empty.')
    elif text[0] == '!stop':
        playlist = []
        message = TextSendMessage(text='The queue is cleared.')
    elif text[0] == '!pause':
        ws = create_connection("ws://videocontrolwebsocket.herokuapp.com", http_proxy_port=80)
        ws.send(json.dumps({"type": "stop"}))
        print("Sent")
        ws.close()
        message = TextSendMessage(text='Music had been paused.')
    elif text[0] == '!start':
        ws = create_connection("ws://videocontrolwebsocket.herokuapp.com", http_proxy_port=80)
        ws.send(json.dumps({"type": "play"}))
        print("Sent")
        ws.close()
        message = TextSendMessage(text='Music is playing.')
    else:
        message = TextSendMessage(text="錯誤的指令，輸入!help以獲取指令列表")
    line_bot_api.reply_message(event.reply_token, message)
import os
if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)


