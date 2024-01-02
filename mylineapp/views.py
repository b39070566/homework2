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

def getNews(n=10):
    url = "https://www.cna.com.tw/list/aall.aspx"
    html = requests.get(url)
    html.encoding ='utf-8'

    soup = BeautifulSoup(html.text, 'html.parser')
    # print(soup.title.string.strip())
    all = soup.find(id='jsMainList').find_all('li')

    rr = ""
    for idx,i in enumerate(all[:n]):
        mlink = i.a.get('href')
        mtext = i.find('h2').text
        mdate = i.find('div',class_='date').text
        rr += " ".join((str(idx+1), mdate, mtext, mlink, "\n"))
    return rr

def getGasolinePrice():
    url = "https://www2.moeaea.gov.tw/oil111"
    html = requests.get(url)
    soup = BeautifulSoup(html.text, 'html.parser')
    price = soup.find_all("div", class_="grid_tab_content")

    pp = price[1].find_all("strong")

    rr = ""
    rr += "92 無鉛汽油 " + pp[0].text +" 元/公升\n"
    rr += "95 無鉛汽油 " + pp[1].text +" 元/公升\n"
    rr += "98 無鉛汽油 " + pp[2].text +" 元/公升\n"
    rr += "超級柴油 " + pp[3].text +" 元/公升"

    return rr

def getInvoice():
    url = "https://invoice.etax.nat.gov.tw"
    html = requests.get(url)
    html.encoding ='utf-8'
    soup = BeautifulSoup(html.text, 'html.parser')

    period = soup.find("a", class_="etw-on")
    rr = period.text+"\n"

    nums = soup.find_all("p", class_="etw-tbiggest")
    rr += "特別獎：" + nums[0].text + "\n"
    rr += "特獎：" + nums[1].text + "\n"
    rr += "頭獎：" + nums[2].text.strip() +" "+ nums[3].text.strip() +" "+ nums[4].text.strip()
    return rr

def start_guess_number():
    global play_nums, ranums
    play_nums = True
    ranums = random.randint(1, 100)
    return TextSendMessage(text="猜數字1-100")

def guess_number(msg):
    global play_nums, ranums
    msg = int(msg)

    if msg > ranums:
        return TextSendMessage(text="小一點")
    elif msg < ranums:
        return TextSendMessage(text="大一點")
    elif msg == ranums:
        play_nums = False
        return TextSendMessage(text="猜中了!")

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
                    reply_message = start_guess_number()
                    line_bot_api.reply_message(event.reply_token, reply_message)
                elif play_nums and msg.isdigit():
                    reply_message = guess_number(msg)
                    line_bot_api.reply_message(event.reply_token, reply_message)
                elif msg == "統一發票" or msg == "發票":
                    Invoice = getInvoice()
                    line_bot_api.reply_message(
                        event.reply_token,
                        TextSendMessage(text=Invoice))
                elif msg == "油價":
                    GasolinePrice = getGasolinePrice()
                    line_bot_api.reply_message(
                        event.reply_token,
                        TextSendMessage(text=GasolinePrice))
                elif msg == "新聞":
                    News = getNews()
                    line_bot_api.reply_message(
                        event.reply_token,
                        TextSendMessage(text=News))
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
