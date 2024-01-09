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

class WordGuessingGame:
    def __init__(self):
        self.playing = False
        self.target_word = ""

    def start_game(self):
        self.playing = True
        # Replace the word list with your own set of words
        word_list = ["apple", "banana", "orange", "grape", "kiwi"]
        self.target_word = random.choice(word_list)
        return TextSendMessage(text="猜單字，詞的長度為{}個字母，請輸入一個字母或整個單字".format(len(self.target_word)))

    def guess(self, user_input):
        if len(user_input) == 1:
            # Guessing a single letter
            if user_input in self.target_word:
                return TextSendMessage(text="正確！{}在單字中".format(user_input))
            else:
                return TextSendMessage(text="錯誤！{}不在單字中".format(user_input))
        elif len(user_input) == len(self.target_word):
            # Guessing the entire word
            if user_input == self.target_word:
                self.playing = False
                return TextSendMessage(text="猜中了！正確答案是{}".format(self.target_word))
            else:
                return TextSendMessage(text="錯誤！猜的單字不正確")
        else:
            return TextSendMessage(text="請輸入一個字母或整個單字")

word_guessing_game = WordGuessingGame()

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

def getNews2(n=3):
    url = "https://www.mnd.gov.tw/"
    html = requests.get(url)
    html.encoding ='utf-8'

    soup = BeautifulSoup(html.text, 'html.parser')
    # print(soup.title.string.strip())
    all = soup.select('#textlb01 ul li')

    rr = ""
    for idx,i in enumerate(all[:n]):
        mlink = i.find('a', class_='headline')['href']
        mtext = i.find('a', class_='headline').text
        mdate = i.find('div', class_='date').text
        rr += " ".join((str(idx + 1), mdate, mtext, mlink, "\n"))
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
                elif msg == "猜單字":
                    returned_message = word_guessing_game.start_game()
                    line_bot_api.reply_message(event.reply_token, returned_message)
                elif word_guessing_game.playing and msg.isalpha():
                    returned_message = word_guessing_game.guess(msg.lower())
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
                elif msg == "軍事":
                    News2 = getNews2()
                    line_bot_api.reply_message(
                        event.reply_token,
                        TextSendMessage(text=News2))
                elif msg == "喵喵":
                    line_bot_api.reply_message(
                        event.reply_token,
                        StickerSendMessage(package_id=1, sticker_id=2))
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
