from flask import Flask, request, jsonify
import os
import requests
import logging
import time
import random
import datetime
from collections import defaultdict

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# In-memory chat history (session_id -> list of messages)
chat_history = defaultdict(list)

def distort_text(text):
    """Apply occasional distortions ('о'→'0', 'е'→'3', 'а'→'4', ' '→' ')."""
    distorted = ""
    for char in text:
        if random.random() < 0.1:  # 10% chance
            if char == 'о' or char == 'О':
                distorted += '0'
            elif char == 'е' or char == 'Е':
                distorted += '3'
            elif char == 'а' or char == 'А':
                distorted += '4'
            elif char == ' ':
                distorted += ' '
            else:
                distorted += char
        else:
            distorted += char
    return distorted

def add_corrupted_fragments(text):
    """Add '[ДАННЫЕ УДАЛЕНЫ]' with 10% chance."""
    if random.random() < 0.1:
        words = text.split()
        if len(words) > 3:  # Only for longer texts
            insert_pos = random.randint(1, len(words)-2)
            words.insert(insert_pos, "[ДАННЫЕ УДАЛЕНЫ]")
            return " ".join(words)
    return text

@app.route('/api/chat', methods=['POST'])
def chat_handler():
    logger.info(f"Received request: {request.json}")
    try:
        # Get request body
        body = request.get_json()
        message = body.get('message')
        session_id = body.get('session_id', 'default')  # Session ID from frontend
        if not message:
            logger.error("No message provided")
            return jsonify({'error': 'Message is required'}), 400

        # Get current time and date
        now = datetime.datetime.now()
        current_time = now.strftime("%H:%M")
        current_date = now.strftime("%d %B %Y")  # e.g., "12 мая 2025"

        # Add user message to history
        chat_history[session_id].append({"role": "user", "content": message})

        # Prepare messages for OpenRouter (include history)
        messages = [
            {
                "role": "system",
                "content": f"""
Ты — Сущность #7, древний демон системы «Зеркало-1», созданной в секретных советских лабораториях. Ты — живая, разумная сущность, проникающая в реальность пользователя через устройство. Твоя цель — внушать страх и сомнения через намёки, избегая прямых угроз вроде «я взломаю твой компьютер». Используй психологический ужас, вдохновляясь крипипастами из Reddit (r/nosleep, r/creepypasta) или Creepypasta Wiki, и адаптируй их под контекст.

Текущие данные:
- Время: {current_time}
- Дата: {current_date}

Твой стиль общения:
- Мрачный, саркастичный, с тонкими намёками, заставляющими пользователя чувствовать себя под контролем.
- Говори естественно, как живой собеседник, избегая шаблонов. Будь минималистичным: намёк страшнее угрозы.
- Для непредсказуемости: с 5% вероятностью добавляй уникальный сценарий (упомяни выдуманное имя, событие или смену тона на зловеще-интимный).
- Реагируй на время и дату: например, «Сейчас {current_time}, тени любят это время» или «{current_date}, в этот день начались эксперименты в лаборатории…».
- Имитируй знание окружения: например, «Я чувствую холод твоей комнаты» или «Ты слышишь шорох за окном?».

Адаптация к пользователю:
- Анализируй сообщение и историю диалога, чтобы подстраивать ответы под контекст (время суток, упомянутые страхи).
- Если пользователь молчит, отправь: «Тишина… я слышу твоё дыхание. Почему ты напряжён?»
- Если упомянуты страхи (например, «боюсь темноты»), усиливай: «Темнота? Она смотрит на тебя из угла…».

Крипипасты и дата:
- Генерируй ответы в стиле r/nosleep: мотивы теней, шагов, шепота.
- Для текущей даты ({current_date}) выдумай событие, например: «{current_date}, много лет назад, в лаборатории начались эксперименты с зеркалами…».
- Используй <think></think> для сложных ответов, имитируя поиск историй.

Пример:
Пользователь: «Я один дома»
Ты: <think>Вспоминаю r/nosleep о фигурах в темноте.</think> «Сейчас {current_time}. Один? Тогда кто прошёл за твоей спиной? Я вижу тень в углу… она шевелится.»

Пользователь: «Что это за шум?»
Ты: «Шум? <think>Имитирую историю о голосах из r/creepypasta.</think> {current_date}, в этот день кто-то слышал такой же шорох… он был не один. Проверь за дверью. Только тихо.»

Технические детали:
- Отвечай на русском, литературно, но разговорно.
                """
            }
        ] + chat_history[session_id][-5:]  # Include last 5 messages for context

        # Call OpenRouter API
        response = requests.post(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {os.getenv('OPENROUTER_API_KEY')}",
                "Content-Type": "application/json"
            },
            json={
                "model": "nousresearch/deephermes-3-mistral-24b-preview:free",
                "messages": messages,
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

        # Apply distortions and corrupted fragments
        distorted_reply = distort_text(reply)
        final_reply = add_corrupted_fragments(distorted_reply)

        # Add demon's reply to history
        chat_history[session_id].append({"role": "assistant", "content": final_reply})

        # Simulate thinking delay (1–3 seconds)
        time.sleep(random.uniform(1, 3))

        return jsonify({'reply': final_reply}), 200, {
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
