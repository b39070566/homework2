from django.shortcuts import render
from django.conf import settings
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseForbidden
from django.views.decorators.csrf import csrf_exempt
import random

from linebot import LineBotApi, WebhookParser
from linebot.exceptions import InvalidSignatureError, LineBotApiError
from linebot.models import MessageEvent, TextSendMessage

line_bot_api = LineBotApi(settings.LINE_CHANNEL_ACCESS_TOKEN)
parser = WebhookParser(settings.LINE_CHANNEL_SECRET)

play_nums = False
ranums = 0
@csrf_exempt
def callback(request):
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
                    ranums = random.randint(1,100)
                    line_bot_api.reply_message(
                        event.reply_token,
                        TextSendMessage(text="猜數字1-100"))
                elif (play_nums) == True:
                    if msg.isdigit():
                        msg = int(msg)
                        if msg > ranums:
                            line_bot_api.reply_message(
                                vent.reply_token,
                                TextSendMessage(text="小一點"))
                        elif msg < ranums:
                            line_bot_api.reply_message(
                                event.reply_token,
                                TextSendMessage(text="大一點"))
                        elif msg == ranums:
                            play_nums = false
                            line_bot_api.reply_message(
                                event.reply_token,
                                TextSendMessage(text="猜中了!"))
                else:
                    line_bot_api.reply_message(
                        event.reply_token,
                        TextSendMessage(text=event.message.text))
                            


                    
                    

        return HttpResponse()
    else:
        return HttpResponseBadRequest()