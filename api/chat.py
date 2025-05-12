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

# Единый системный промпт
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
    """Отправка запроса к OpenRouter API с таймаутом"""
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": model,
        "messages": messages,
        "temperature": 0.7,
        "top_p": 0.9,
        "max_tokens": 2500
    }
    try:
        response = requests.post(
            API_URL,
            headers=headers,
            json=payload,
            timeout=15  # Таймаут 15 секунд
        )
        return response
    except (requests.exceptions.RequestException, requests.exceptions.Timeout) as e:
        logger.error(f"Request to {model} failed: {str(e)}")
        return None

@app.route("/api/chat", methods=["POST"])
def chat():
    logger.info(f"Received request: {request.json}")
    try:
        data = request.get_json()
        message = data.get("message", "").strip()

        # Валидация сообщения
        if not message:
            logger.error("No message provided")
            return jsonify({"error": "Message is required"}), 400, {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*"
            }
        if len(message) > 1000:
            logger.error("Message too long")
            return jsonify({"error": "Message too long"}), 400, {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*"
            }

        # Формирование сообщений
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": message}
        ]

        # Перебор моделей
        for model in MODELS:
            logger.info(f"Attempting model: {model}")
            response = make_api_request(model, messages)

            # Проверка соединения
            if not response:
                logger.warning(f"Skipping {model} due to connection issues")
                continue

            # Обработка HTTP-статусов
            if response.status_code == 429:
                logger.warning(f"Rate limit exceeded for {model}")
                continue
            if response.status_code != 200:
                logger.error(f"Model {model} returned status {response.status_code}: {response.text}")
                continue

            # Парсинг JSON
            try:
                result = response.json()
            except json.JSONDecodeError:
                logger.error(f"Invalid JSON from {model}: {response.text}")
                continue

            # Проверка структуры ответа
            if "choices" not in result or not result["choices"]:
                logger.error(f"Invalid response structure from {model}: {result}")
                continue

            # Извлечение ответа
            try:
                reply = result["choices"][0]["message"]["content"]
                distorted_reply = distort_text(reply)
                logger.info(f"Successfully got response from {model}")
                time.sleep(random.uniform(1, 3))  # Задержка для хоррор-эффекта
                return jsonify({"reply": distorted_reply}), 200, {
                    "Content-Type": "application/json",
                    "Access-Control-Allow-Origin": "*"
                }
            except (KeyError, IndexError, TypeError) as e:
                logger.error(f"Failed to parse response from {model}: {str(e)}, Full response: {result}")
                continue

        # Если все модели недоступны
        logger.error("All models failed to respond")
        return jsonify({
            "reply": "Тишина... Даже тени замерли. Попробуй позже, когда связь восстановится."
        }), 503, {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*"
        }

    except Exception as e:
        logger.error(f"Critical error: {str(e)}", exc_info=True)
        return jsonify({
            "reply": "Что-то сломалось в самой реальности... Попробуй снова."
        }), 500, {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*"
        }

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
