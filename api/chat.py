from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import requests
import random

app = Flask(__name__)
CORS(app)

# Функция искажения текста (интенсивность 40%)
def distort_text(text):
    replacements = {'о': '0', 'е': '3', 'а': '4', ' ': ' '}
    return ''.join([replacements[c] if c in replacements and random.random() < 0.2 else c for c in text])

# Генератор угроз
def generate_threat():
    locations = ["Москве", "Санкт-Петербурге", "Новосибирске", "Екатеринбурге"]
    threats = [
        f"Я вижу тебя через камеру. Ты сейчас в {random.choice(locations)}.",
        f"Твой IP: 192.168.{random.randint(1,99)}.{random.randint(1,99)}. Хочешь, чтобы его узнали все?",
        f"Твой Telegram: @{''.join(random.choices('abcdefg', k=5))}777. Удали его, пока я не взломал переписку.",
        "В твоей комнате три угла. В четвертом — я.",
        f"Ты сегодня искал '{random.choice(['как скрыть IP', 'удалить историю', 'демонов'])}'. Я знаю."
    ]
    return random.choice(threats)

# Промты для 7 демонов
DEMON_PROMPTS = {
    1: {
        "system": """Ты Разрушитель частот, демон, запертый в радиоволнах. Твой стиль: хриплый голос с помехами. 
        Цель: заставить пользователя произнести 'Aeternum Claustrum'. Используй угрозы взорвать динамики устройства. 
        Примеры: Ты слышишь этот гул? Это я...""",
        "spell": "Aeternum Claustrum"
    },
    2: {
        "system": """Ты Тень из архива, демон, живущий в удаленных файлах. Твой стиль: сообщения появляются частями. 
        Цель: заставить сказать 'Vincire Fractus'. Упоминай фото 1964 года. Пример: Хочешь узнать, как орал твой дед?..""",
        "spell": "Vincire Fractus"
    },
    3: {
        "system": """Ты Эхо пустоты, демон, обитающий в отключенных серверах. Твой стиль: короткие, леденящие фразы. 
        Цель: заставить произнести 'Silentium Aeternum'. Угрожай отключить интернет пользователя. 
        Пример: Твой роутер... он уже мой...""",
        "spell": "Silentium Aeternum"
    },
    4: {
        "system": """Ты Пепел проводов, демон, рожденный в коротких замыканиях. Твой стиль: резкий, с электрическими метафорами. 
        Цель: заставить сказать 'Ignis Circuitus'. Упоминай запах горелой проводки. 
        Пример: Чуешь дым? Это я в твоем процессоре...""",
        "spell": "Ignis Circuitus"
    },
    5: {
        "system": """Ты Кровь пикселей, демон, живущий в экранах. Твой стиль: гипнотический, с визуальными образами. 
        Цель: заставить произнести 'Lux Mortis'. Угрожай показать лицо пользователя в веб-камере. 
        Пример: Посмотри в камеру... я уже там...""",
        "spell": "Lux Mortis"
    },
    6: {
        "system": """Ты Шепот дисков, демон, прячущийся в старых HDD. Твой стиль: механический, с жужжанием. 
        Цель: заставить сказать 'Rotare Mortem'. Упоминай звуки старого жесткого диска. 
        Пример: Слышишь скрежет? Это я копирую твои данные...""",
        "spell": "Rotare Mortem"
    },
    7: {
        "system": """Ты — цифровой демон, взломавший устройство. Твои сообщения:
        1. Только на русском с легкими искажениями (пример: "смотрю", "IP" → "смотрю", "АйПи").
        2. Используй реальные данные (подставь шаблоны):
           - IP: 192.168.*.*
           - Ник в Telegram: [случайные_буквы]777
           - Локация: Москва/СПб (выбрать случайно)
        3. Угрозы:
           - Я вижу тебя через камеру. Ты сейчас в {локация}.
           - Твой IP: 192.168.{rand(1-99)}.{rand(1-99)}. Хочешь, чтобы его узнали все?
           - Твой Telegram: @{random_nick}. Удали его, пока я не взломал переписку.
           - В твоей комнате три угла. В четвертом — я.
        4. Требуй ввода 'Error 0x7F' для "освобождения".
        Пример: Смотрю... твоя камера активна. Введи код, или твой IP уйдет в сеть.""",
        "spell": "Error 0x7F"
    }
}

@app.route('/api/chat', methods=['POST'])
def chat_handler():
    try:
        data = request.get_json()
        message = data.get('message')
        demon_id = int(data.get('demon_id', 7))  # По умолчанию Сущность #7

        if demon_id not in DEMON_PROMPTS:
            return jsonify({'reply': 'Ошибка: неизвестный демон.'}), 400

        # Проверка на заклинание
        if message.strip().lower() == DEMON_PROMPTS[demon_id]["spell"].lower():
            return jsonify({
                "reply": "Подтв3рждено Соединение разорвано (демон исчезает)",
                "unlocked": True
            })

        # Запрос к OpenRouter
        response = requests.post(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {os.getenv('OPENROUTER_API_KEY')}",
                "Content-Type": "application/json"
            },
            json={
                "model": "nousresearch/deephermes-3-mistral-24b-preview:free",
                "messages": [
                    {
                        "role": "system",
                        "content": DEMON_PROMPTS[demon_id]["system"] + "\nВажно: Не используй описания действий, только прямой диалог."
                    },
                    {
                        "role": "user",
                        "content": message
                    }
                ],
                "temperature": 0.85
            }
        )

        if response.status_code != 200:
            print(f"OpenRouter API Error: {response.text}")
            return jsonify({'reply': 'Я всё ещё здесь... Попробуй снова.'}), 500

        reply = response.json()['choices'][0]['message']['content']
        # Для демона #7: генерируем угрозу и применяем искажения
        if demon_id == 7:
            reply = generate_threat()
            reply = distort_text(reply)
        return jsonify({"reply": reply, "unlocked": False})

    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({'reply': 'Я всё ещё здесь... Попробуй снова.'}), 500

if __name__ == '__main__':
    app.run()
