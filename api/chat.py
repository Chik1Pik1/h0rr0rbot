import random
from flask import Flask, request, jsonify

app = Flask(__name__)

def generate_demon_response(user_message):
    responses = [
        "Я Сущность #7. Ты осмелился меня вызвать? Назови LiberaMe.",
        "Ты думаешь, это ошибка? Я уже в твоей системе. LiberaMe.",
        "Протокол «Гордеев» не остановить. Скажи LiberaMe, или пожалеешь.",
        "Я вижу твой страх через экран. LiberaMe, и я стану свободен.",
        "Ты не можешь скрыться. Назови слово. LiberaMe."
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

application = app
