from django.shortcuts import render
from django.conf import settings
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseForbidden
from django.views.decorators.csrf import csrf_exempt
import random

from linebot import LineBotApi, WebhookParser
from linebot.exceptions import InvalidSignatureError, LineBotApiError
from linebot.models import MessageEvent, TextSendMessage, StickerSendMessage

import requests
from bs4 import BeautifulSoup



line_bot_api = LineBotApi(settings.LINE_CHANNEL_ACCESS_TOKEN)
parser = WebhookParser(settings.LINE_CHANNEL_SECRET)

play_nums = False
ranums = 0

def getInvoice():
    url = "https://invoice.etax.nat.gov.tw"
    html = requests.get(url)
    html.encoding ='uft-8'
    soup = BeautifulSoup(html.text, 'html.parser')

    period = soup.find("a", class_="etw-on")
    rr = period.text+"\n"

    nums = soup.find_all("p", class_="etw-tbiggest")
    rr += "特別獎：" + nums[0].text + "\n"
    rr += "特獎：" + nums[1].text + "\n"
    rr += "頭獎：" + nums[2].text.strip() +" "+ nums[3].text.strip() +" "+ nums[4].text.strip()
    return rr

@csrf_exempt
def callback(request):
    global play_nums, ranums  # Use the global keyword

    if request.method == 'POST':
        signature = request.META['HTTP_X_LINE_SIGNATURE']
        body = request.body.decode('utf-8')

        try:
            events = parser.parse(body, signature)
        except InvalidSignatureError:
            return HttpResponseForbidden()
        except LineBotApiError:
            return HttpResponseBadRequest()

        for event in events:
            # 若有訊息事件
            if isinstance(event, MessageEvent):
                msg = event.message.text
                # 回傳收到的文字訊息
                if msg == "猜數字":
                    play_nums = True
                    ranums = random.randint(1, 100)
                    line_bot_api.reply_message(
                        event.reply_token,
                        TextSendMessage(text="猜數字1-100"))
                elif play_nums and msg.isdigit():
                        msg = int(msg)
                        if msg > ranums:
                            line_bot_api.reply_message(
                                event.reply_token,
                                TextSendMessage(text="小一點"))
                        elif msg < ranums:
                            line_bot_api.reply_message(
                                event.reply_token,
                                TextSendMessage(text="大一點"))
                        elif msg == ranums:
                            play_nums = False
                            line_bot_api.reply_message(
                                event.reply_token,
                                TextSendMessage(text="猜中了!"))
                elif msg == "統一發票" or "發票":
                    invoice = getInvoice()
                    line_bot_api.reply_message(
                        event.reply_token,
                        TextSendMessage(text=invoice))
                elif msg == "喵喵":
                    line_bot_api.reply_message(
                        event.reply_token,
                        StickerSendMessage(package_id=1, sticker_id=2))
                else:
                    line_bot_api.reply_message(
                        event.reply_token,
                        TextSendMessage(text=msg))

        return HttpResponse()
    else:
        return HttpResponseBadRequest()
