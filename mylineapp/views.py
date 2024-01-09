from django.shortcuts import render
from django.conf import settings
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseForbidden
from django.views.decorators.csrf import csrf_exempt
import random

from linebot import LineBotApi, WebhookParser
from linebot.exceptions import InvalidSignatureError, LineBotApiError
from linebot.models import MessageEvent, TextSendMessage, StickerSendMessage, ImageSendMessage, AudioSendMessage, VideoSendMessage

import requests
from bs4 import BeautifulSoup



line_bot_api = LineBotApi(settings.LINE_CHANNEL_ACCESS_TOKEN)
parser = WebhookParser(settings.LINE_CHANNEL_SECRET)

class NumberGuessingGame:
    def __init__(self):
        self.playing = False
        self.target_number = 0

    def start_game(self):
        self.playing = True
        self.target_number = random.randint(1, 100)
        return TextSendMessage(text="猜數字1-100")

    def guess(self, user_input):
        user_guess = int(user_input)

        if user_guess > self.target_number:
            return TextSendMessage(text="小一點")
        elif user_guess < self.target_number:
            return TextSendMessage(text="大一點")
        elif user_guess == self.target_number:
            self.playing = False
            return TextSendMessage(text="猜中了!")

number_guessing_game = NumberGuessingGame()

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
                    returned_message = number_guessing_game.start_game()
                    line_bot_api.reply_message(event.reply_token, returned_message)
                elif number_guessing_game.playing and msg.isdigit():
                    returned_message = number_guessing_game.guess(msg)
                    line_bot_api.reply_message(event.reply_token, returned_message)
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
                elif msg == "影片":
                    line_bot_api.reply_message(
                        event.reply_token,
                        VideoSendMessage(original_content_url='./vid.mp4',
                        preview_image_url='data:image/jpeg;base64,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'))
                elif msg == "林襄":
                    image_urls = [
                        'https://s.yimg.com/ny/api/res/1.2/qGUq9eZftFfkgDwA6J8mcQ--/YXBwaWQ9aGlnaGxhbmRlcjt3PTk2MDtoPTE0NDA7Y2Y9d2VicA--/https://media.zenfs.com/ko/news_tvbs_com_tw_938/0b727f92c662723bd9941fcaac52b5bd',
                        'https://attach.setn.com/newsimages/2022/09/01/3805758-PH.jpg',
                        'https://images.chinatimes.com/newsphoto/2023-11-03/1024/20231103003058.jpg',
                        'https://s.yimg.com/ny/api/res/1.2/H_z17aILl883n2Nz5cxrTA--/YXBwaWQ9aGlnaGxhbmRlcjt3PTY0MDtoPTgwMQ--/https://media.zenfs.com/zh-tw/setn.com.tw/3ef844aae990f868d9e0fadf19ee72fe',
                        'https://obs.line-scdn.net/0hMr3CcEnQEl0OOgaykLhtCjZsHiw9XAhULAxcaSw7Hj8hFlZYYQxBPi5uSHFwXgIMLgsObCpqH20gCQULMw/w1200',
                    ]
                    selected_image_url = random.choice(image_urls)

                    line_bot_api.reply_message(
                        event.reply_token,
                        ImageSendMessage(original_content_url=selected_image_url,
                        preview_image_url=selected_image_url))
                else:
                    line_bot_api.reply_message(
                        event.reply_token,
                        TextSendMessage(text=msg))

        return HttpResponse()
    else:
        return HttpResponseBadRequest()
