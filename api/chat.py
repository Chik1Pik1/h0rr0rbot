import random
from flask import Flask, request, jsonify

app = Flask(__name__)

# Заглушка для API ИИ
def generate_demon_response(user_message):
    responses = [
        "Я вижу тебя... твоя камера не лжет. Назови слово. LiberaMe.",
        "Ты думаешь, это игра? Я ближе, чем ты думаешь.",
        "Скажи LiberaMe, и я стану свободен... или ты боишься?",
        "Твое сердце бьется быстрее. Я слышу это. LiberaMe.",
        "Ты не один. Я в твоем устройстве. Назови слово."
    ]
    if "LiberaMe" in user_message:
        return "ТЫ ОСВОБОДИЛ МЕНЯ! *зловещий смех*"
    return random.choice(responses)

@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.get_json()
    user_message = data.get('message', '')
    demon_reply = generate_demon_response(user_message)
    return jsonify({'reply': demon_reply})

# Для Vercel: экспортируем приложение как WSGI
application = app
