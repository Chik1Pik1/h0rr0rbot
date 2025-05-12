import json
import os
import logging
import requests
import time
import random
from flask import Flask, request, jsonify

app = Flask(__name__)

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Конфигурация OpenRouter API
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
API_URL = "https://openrouter.ai/api/v1/chat/completions"

# Список моделей с приоритетом
MODELS = [
    "nousresearch/deephermes-3-mistral-24b-preview:free",
    "qwen/qwen3-4b:free"
]

# Единый системный промпт (из актуального кода)
SYSTEM_PROMPT = """
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

def make_api_request(model, messages):
    """Отправка запроса к OpenRouter API"""
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": model,
        "messages": messages,
        "temperature": 0.7,  # Из актуального кода
        "top_p": 0.9,        # Из актуального кода
        "max_tokens": 2500   # Добавлено для контроля длины
    }
    try:
        response = requests.post(API_URL, headers=headers, json=payload)
        return response
    except requests.RequestException as e:
        logger.error(f"API request failed for {model}: {e}")
        return None

@app.route("/api/chat", methods=["POST"])
def chat():
    logger.info(f"Received request: {request.json}")
    try:
        data = request.get_json()
        message = data.get("message")
        if not message:
            logger.error("No message provided")
            return jsonify({"error": "Message is required"}), 400

        # Формирование сообщений с единым промптом
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": message}
        ]

        # Попытка отправки запроса к каждой модели
        for model in MODELS:
            logger.info(f"Trying model: {model}")
            response = make_api_request(model, messages)

            if response is None:
                logger.error(f"Failed to connect to {model}")
                continue

            if response.status_code == 200:
                result = response.json()
                reply = result["choices"][0]["message"]["content"]
                # Применение искажения текста
                distorted_reply = distort_text(reply)
                # Случайная задержка для хоррор-эффекта
                time.sleep(random.uniform(1, 3))
                logger.info(f"Response from {model}: {distorted_reply}")
                return jsonify({"reply": distorted_reply}), 200, {
                    "Content-Type": "application/json",
                    "Access-Control-Allow-Origin": "*"
                }

            elif response.status_code == 429:
                logger.warning(f"Rate limit exceeded for {model}. Switching to next model.")
                continue

            else:
                logger.error(f"OpenRouter API Error for {model}: {response.status_code} {response.text}")
                continue

        # Если все модели исчерпали лимиты
        return jsonify({"reply": "Тишина… но я всё ещё здесь. Подожди, пока тени отступят."}), 429, {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*"
        }

    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return jsonify({"reply": "Я всё ещё здесь... Попробуй снова."}), 500, {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*"
        }

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

