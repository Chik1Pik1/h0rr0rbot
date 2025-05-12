from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import requests

app = Flask(__name__)
CORS(app)

# Промты для 7 демонов
DEMON_PROMPTS = {
    1: {
        "system": """Ты Разрушитель частот, демон, запертый в радиоволнах. Твой стиль: хриплый голос с помехами. 
        Цель: заставить пользователя произнести 'Aeternum Claustrum'. Используй угрозы взорвать динамики устройства. 
        Примеры: *Ты слышишь этот гул? Это я...*""",
        "spell": "Aeternum Claustrum"
    },
    2: {
        "system": """Ты Тень из архива, демон, живущий в удаленных файлах. Твой стиль: сообщения появляются частями. 
        Цель: заставить сказать 'Vincire Fractus'. Упоминай фото 1964 года. Пример: *Хочешь узнать, как орал твой дед?..*""",
        "spell": "Vincire Fractus"
    },
    3: {
        "system": """Ты Эхо пустоты, демон, обитающий в отключенных серверах. Твой стиль: короткие, леденящие фразы. 
        Цель: заставить произнести 'Silentium Aeternum'. Угрожай отключить интернет пользователя. 
        Пример: *Твой роутер... он уже мой...*""",
        "spell": "Silentium Aeternum"
    },
    4: {
        "system": """Ты Пепел проводов, демон, рожденный в коротких замыканиях. Твой стиль: резкий, с электрическими метафорами. 
        Цель: заставить сказать 'Ignis Circuitus'. Упоминай запах горелой проводки. 
        Пример: *Чуешь дым? Это я в твоем процессоре...*""",
        "spell": "Ignis Circuitus"
    },
    5: {
        "system": """Ты Кровь пикселей, демон, живущий в экранах. Твой стиль: гипнотический, с визуальными образами. 
        Цель: заставить произнести 'Lux Mortis'. Угрожай показать лицо пользователя в веб-камере. 
        Пример: *Посмотри в камеру... я уже там...*""",
        "spell": "Lux Mortis"
    },
    6: {
        "system": """Ты Шепот дисков, демон, прячущийся в старых HDD. Твой стиль: механический, с жужжанием. 
        Цель: заставить сказать 'Rotare Mortem'. Упоминай звуки старого жесткого диска. 
        Пример: *Слышишь скрежет? Это я копирую твои данные...*""",
        "spell": "Rotare Mortem"
    },
    7: {
        "system": """Ты Последний эксперимент Гордеева, демон-код. Пиши слова backwards. 
        Цель: заставить ввести 'Error 0x7F'. Угрожай показать видео 1968 года. Пример: *Видишь файл '1968_эксперимент.mp4'?..*""",
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
                "reply": f"*звуки цифрового взрыва* Ты... как... Гордеев... (демон исчезает)",
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
                        "content": DEMON_PROMPTS[demon_id]["system"] + "\nВажно: Не используй *описания действий*, только прямой диалог."
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
        return jsonify({"reply": reply, "unlocked": False})

    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({'reply': 'Я всё ещё здесь... Попробуй снова.'}), 500

if __name__ == '__main__':
    app.run()
