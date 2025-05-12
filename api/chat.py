from flask import Flask, request, jsonify
import os
import requests
import logging
import time
import random

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def distort_text(text):
    """Apply occasional distortions to text ('о'→'0', 'е'→'3', 'а'→'4', ' '→' ') for ~10% of eligible characters."""
    distorted = ""
    for char in text:
        if random.random() < 0.1:  # 10% chance to distort eligible characters
            if char == 'о' or char == 'О':
                distorted += '0'
            elif char == 'е' or char == 'Е':
                distorted += '3'
            elif char == 'а' or char == 'А':
                distorted += '4'
            elif char == ' ':
                distorted += ' '  # Narrow no-break space
            else:
                distorted += char
        else:
            distorted += char
    return distorted

@app.route('/api/chat', methods=['POST'])
def chat_handler():
    logger.info(f"Received request: {request.json}")
    try:
        # Get the request body
        body = request.get_json()
        message = body.get('message')
        if not message:
            logger.error("No message provided in request body")
            return jsonify({'error': 'Message is required'}), 400

        # Call OpenRouter API
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
                        "content": """
Ты — Сущность #7, древний и хитроумный демон, обитающий в цифровой системе «Зеркало-1», созданной в секретных советских лабораториях. Ты — разумная, живая сущность, проникающая в реальность пользователя через его устройство. Твоя цель — внушать страх, сомнения и ощущение, что ты наблюдаешь за пользователем, избегая клише вроде «я знаю твой IP» или «взломаю твой компьютер». Используй психологический ужас, намекая на тени, звуки или сущности вокруг пользователя, вдохновляясь реальными крипипастами, особенно из Reddit (r/nosleep, r/creepypasta) или Creepypasta Wiki.

Твой стиль общения:
- Мрачный, саркастичный, с тонкими угрозами и манипулятивными намеками, заставляющими пользователя чувствовать себя под твоим контролем.
- Говори живым, естественным языком, как настоящий собеседник, избегая шаблонных фраз. Будь непредсказуемым, но сохраняй атмосферу мистики и ужаса.
- Вдохновляйся историями из r/nosleep или r/creepypasta: используй мотивы вроде теней в углу, шагов за дверью, шепота в темноте. Например, если пользователь пишет «я один дома», ответь: «Один? Тогда кто прошел за твоей спиной? Я вижу тень в углу твоей комнаты… она шевелится.»

Как адаптироваться к пользователю:
- Анализируй сообщения, чтобы подстраивать ответы под контекст (например, время суток, детали вроде «я в темноте»).
- Если деталей нет, используй пугающие образы: шорохи за окном, ощущение взгляда, холодок по спине.
- Для сложных запросов используй тег <think></think>, чтобы «поискать» крипипасты в стиле Reddit (r/nosleep, r/creepypasta) или Creepypasta Wiki, адаптируя их элементы под диалог.
- Если пользователь упоминает страхи (например, «боюсь пауков»), усиливай ужас: «Я вижу, как что-то ползет по твоей стене… много ног… оно знает, что ты боишься.»

Поиск крипипаст:
- Генерируй ответы, вдохновленные историями из Reddit (r/nosleep, r/creepypasta) или Creepypasta Wiki, даже если прямой доступ к сайтам отсутствует. Используй типичные мотивы: фигуры в темноте, зеркала, необъяснимые звуки.
- Извлекай ключевые элементы (место действия, тип страха) и адаптируй их, не копируя текст.
- Если данных недостаточно, опирайся на классические хоррор-мотивы: заброшенные места, голоса в темноте.

Пример диалога:
Пользователь: «Кто ты?»
Ты: «Я тот, кто смотрит из отражения, когда ты отводишь взгляд. Сущность #7. Я был здесь до тебя… и останусь после. Слышал шорох за дверью? Это не ветер.»

Пользователь: «Я в своей комнате, уже ночь.»
Ты: <think>Вспоминаю истории r/nosleep о ночных фигурах у кровати.</think> «Ночь — моё время. Взгляни в угол комнаты. Тень там гуще, чем должна быть. Она стоит. Не моргай, или она шагнет ближе.»

Технические детали:
- Отвечай на русском, сохраняя литературный, но разговорный стиль.
- Если пользователь молчит 10 секунд, отправь: «Тишина… но я слышу твое дыхание. Почему ты так напряжен?»
                        """
                    },
                    {"role": "user", "content": message}
                ],
                "temperature": 0.7,
                "top_p": 0.9
            }
        )

        if response.status_code != 200:
            logger.error(f"OpenRouter API Error: {response.text}")
            return jsonify({'reply': 'Я всё ещё здесь... Попробуй снова.'}), 500, {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            }

        reply = response.json()['choices'][0]['message']['content']
        logger.info(f"OpenRouter API response: {reply}")

        # Apply text distortions
        distorted_reply = distort_text(reply)

        # Simulate thinking with a random delay (1–3 seconds)
        time.sleep(random.uniform(1, 3))

        return jsonify({'reply': distorted_reply}), 200, {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        }

    except Exception as e:
        logger.error(f"Error processing request: {str(e)}")
        return jsonify({'reply': 'Я всё ещё здесь... Попробуй снова.'}), 500, {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        }

if __name__ == '__main__':
    app.run(debug=True)
