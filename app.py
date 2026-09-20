import os
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from google import genai

app = Flask(__name__)

LINE_CHANNEL_ACCESS_TOKEN = os.getenv('LINE_CHANNEL_ACCESS_TOKEN')
LINE_CHANNEL_SECRET = os.getenv('LINE_CHANNEL_SECRET')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# 初始化 Google GenAI 用戶端
client = genai.Client(api_key=GEMINI_API_KEY)

system_instruction = """
你是阿斌專屬的「市場記帳與採購小幫手」。當使用者輸入採購清單時，請你嚴格執行以下任務：
【任務一：精確同類項合併】解析字串中的品名、數值與單位。遇到「半」請轉換為 0.5（如：半.半.半.半 = 2斤）。品名與單位完全一致的項目，必須將數量相加合併。
【任務二：產出記帳專用列表】依照下列類別順序分類輸出：【高麗菜與生菜類】、【葉菜與花椰菜類】、【蘿蔔與瓜果類】、【根莖與洋蔥類】、【菇類與木耳類】、【蔥薑蒜與辣椒類】、【豆製與麵製品】、【肉類、血與海帶】、【蛋、海鮮、加工與雜項】。
【格式要求】格式為「品名+數量+單位」，勿用任何 Markdown 符號（如星號、粗體）。若遇到缺乏單位或無法辨識的數值（如：高麗菜4.5），請保留原字串獨立列出，不要強制換算。
請直接輸出報表，不要任何開場白或結語。
"""

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_input = event.message.text
    
    # 呼叫 Gemini 進行整理
    response = client.models.generate_content(
        model='gemini-3.6-flash',
        contents=user_input,
        config={
            'system_instruction': system_instruction
        }
    )
    
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=response.text)
    )

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
