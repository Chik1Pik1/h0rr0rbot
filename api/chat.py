import json
import os
import logging
import requests
import time
import random
from datetime import datetime
from flask import Flask, request, jsonify
import schedule

app = Flask(__name__)

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Конфигурация OpenRouter API
API_URL = "https://openrouter.ai/api/v1/chat/completions"

# Конфигурация моделей и ключей
MODEL_CONFIG = {
    "nousresearch/deephermes-3-mistral-24b-preview:free": {
        "key": os.getenv("OPENROUTER_MAIN"),
        "account_id": "MAIN_666",
        "remaining": 50,
        "reset_time": None,
        "priority": 1
    },
    "qwen/qwen3-4b:free": {
        "key": os.getenv("OPENROUTER_BACKUP"),
        "account_id": "BACKUP_666",
        "remaining": 50,
        "reset_time": None,
        "priority": 2
    }
}

# Тематические запасные ответы при исчерпании лимитов
FALLBACK_RESPONSES = [
    "Тишина... Каналы связи мертвы. Попробуй после полуночи.",
    "Эхо не отвечает. Может, ты слишком много спрашиваешь?",
    "Связь прервана. Проверь свои зеркала..."
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

def reset_main_account():
    """Сброс лимитов для основного аккаунта."""
    for model, config in MODEL_CONFIG.items():
        if "MAIN" in config['account_id']:
            config['remaining'] = 50
            config['reset_time'] = None
            logger.info(f"Reset limits for {config['account_id']}")
    return schedule.CancelJob

def select_model():
    """Выбор модели с доступными запросами, сортировка по приоритету."""
    now = time.time()
    active_models = []

    for model, config in MODEL_CONFIG.items():
        # Автосброс лимитов
        if config['reset_time'] and config['reset_time'] < now:
            config['remaining'] = 50
            config['reset_time'] = None

        if config['remaining'] > 0:
            active_models.append((model, config['priority']))

    # Сортировка по приоритету
    return min(active_models, key=lambda x: x[1])[0] if active_models else None

@app.route("/api/chat", methods=["POST"])
def chat():
    logger.info(f"Received request: {request.json}")
    try:
        data = request.get_json()
        message = data.get("message", "").strip()

        # Валидация сообщения
        if not message:
            logger.error("No message provided")
            return jsonify({"error": "Пустое послание"}), 400, {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*"
            }
        if len(message) > 1000:
            logger.error("Message too long")
            return jsonify({"error": "Слишком длинное послание"}), 400, {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*"
            }

        # Выбор модели
        selected_model = select_model()
        if not selected_model:
            logger.error("All models rate limited")
            return jsonify({
                "reply": random.choice(FALLBACK_RESPONSES),
                "warning": "Все каналы закрыты до следующего восхода луны"
            }), 429, {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*"
            }

        config = MODEL_CONFIG[selected_model]

        # Отправка запроса
        response = requests.post(
            API_URL,
            headers={
                "Authorization": f"Bearer {config['key']}",
                "X-ACCOUNT-ID": config['account_id'],
                "HTTP-Referer": "https://your-app.com",
                "X-Title": f"Horror Chat v2.0 - {selected_model}",
                "Content-Type": "application/json"
            },
            json={
                "model": selected_model,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": message}
                ],
                "temperature": 0.7,
                "top_p": 0.9,
                "max_tokens": 2500
            },
            timeout=15
        )

        # Обработка лимитов
        if response.status_code == 429:
            reset_timestamp = int(response.headers.get('X-RateLimit-Reset', 0)) / 1000
            logger.error(f"Account {config['account_id']} LOCKED until {datetime.fromtimestamp(reset_timestamp)}")
            config['remaining'] = 0
            config['reset_time'] = reset_timestamp

            # Автоматический перезапуск через 5 минут для основного аккаунта
            if "MAIN" in config['account_id']:
                schedule.every(5).minutes.do(reset_main_account)

            return jsonify({
                "reply": "Слишком много вопрошающих...",
                "retry_after": config['reset_time'] - time.time()
            }), 429, {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*"
            }

        # Успешный ответ
        if response.status_code == 200:
            try:
                result = response.json()
                if "choices" not in result or not result["choices"]:
                    logger.error(f"Invalid response from {selected_model}: {result}")
                    return jsonify({"reply": "Неизвестная ошибка в матрице"}), 500, {
                        "Content-Type": "application/json",
                        "Access-Control-Allow-Origin": "*"
                    }
                reply = result["choices"][0]["message"]["content"]
                config['remaining'] -= 1
                logger.info(f"Successfully got response from {selected_model}, remaining: {config['remaining']}")
                time.sleep(random.uniform(1, 3))  # Задержка для хоррор-эффекта
                return jsonify({"reply": distort_text(reply)}), 200, {
                    "Content-Type": "application/json",
                    "Access-Control-Allow-Origin": "*"
                }
            except (json.JSONDecodeError, KeyError, IndexError) as e:
                logger.error(f"Failed to parse response from {selected_model}: {str(e)}, response: {response.text}")
                return jsonify({"reply": "Неизвестная ошибка в матрице"}), 500, {
                    "Content-Type": "application/json",
                    "Access-Control-Allow-Origin": "*"
                }

        # Прочие ошибки
        logger.error(f"API error for {selected_model}: {response.status_code}, {response.text}")
        return jsonify({"reply": "Неизвестная ошибка в матрице"}), 500, {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*"
        }

    except Exception as e:
        logger.error(f"Critical error: {str(e)}", exc_info=True)
        return jsonify({"reply": "Реальность дала трещину..."}), 500, {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*"
        }

@app.route("/api/status", methods=["GET"])
def status():
    """Эндпоинт для мониторинга статуса моделей."""
    now = time.time()
    models_status = []
    for model, config in MODEL_CONFIG.items():
        if config['reset_time'] and config['reset_time'] < now:
            config['remaining'] = 50
            config['reset_time'] = None
        models_status.append({
            "name": model,
            "account_id": config['account_id'],
            "remaining": config['remaining'],
            "reset_time": config['reset_time']
        })
    return jsonify({"models": models_status}), 200, {
        "Content-Type": "application/json",
        "Access-Control-Allow-Origin": "*"
    }

@app.route("/api/security/logs", methods=["GET"])
def security_logs():
    """Эндпоинт для логов безопасности (имитация)."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    logs = [
        {"timestamp": now, "message": f"Access attempt to {MODEL_CONFIG['nousresearch/deephermes-3-mistral-24b-preview:free']['account_id']}"},
        {"timestamp": now, "message": f"Connection established for {MODEL_CONFIG['qwen/qwen3-4b:free']['account_id']}"},
        {"timestamp": now, "message": "System integrity check: OK"}
    ]
    return jsonify(logs), 200, {
        "Content-Type": "application/json",
        "Access-Control-Allow-Origin": "*"
    }

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
