from flask import Flask, request, jsonify
import os
import requests
import logging
import time
import random
from supabase import create_client, Client
from datetime import datetime
import pytz

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Supabase client
supabase: Client = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_ANON_KEY")
)

# Load API keys and models
API_KEYS = [
    {
        "key": os.getenv("OPENROUTER_API_KEY_1"),
        "model": os.getenv("OPENROUTER_MODEL_1", "nousresearch/deephermes-3-mistral-24b-preview:free"),
        "name": "primary"
    },
    {
        "key": os.getenv("OPENROUTER_API_KEY_2"),
        "model": os.getenv("OPENROUTER_MODEL_2", "qwen/qwen3-4b:free"),
        "name": "secondary"
    }
]

REQUEST_LIMIT = 50  # Daily request limit (per user)

# Dictionary for Russian month names
RUSSIAN_MONTHS = {
    1: "января",
    2: "февраля",
    3: "марта",
    4: "апреля",
    5: "мая",
    6: "июня",
    7: "июля",
    8: "августа",
    9: "сентября",
    10: "октября",
    11: "ноября",
    12: "декабря"
}

def distort_text(text):
    """Apply occasional distortions to text ('о'→'0', 'е'→'3', 'а'→'4', ' '→' ') for ~10% of eligible characters."""
    distorted = ""
    for char in text:
        if random.random() < 0.1:
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

def get_request_counter(user_id):
    """Get or initialize request counter for a user."""
    today = str(datetime.now(pytz.timezone('Europe/Moscow')).date())
    counter = supabase.table("request_counter").select("*").eq("user_id", user_id).eq("last_reset_date", today).execute()
    
    if not counter.data:
        supabase.table("request_counter").insert({
            "user_id": user_id,
            "request_count": 0,
            "last_reset_date": today
        }).execute()
        return 0
    return counter.data[0]["request_count"]

def increment_request_counter(user_id):
    """Increment request counter for a user."""
    today = str(datetime.now(pytz.timezone('Europe/Moscow')).date())
    counter = supabase.table("request_counter").select("*").eq("user_id", user_id).eq("last_reset_date", today).execute()
    
    if counter.data:
        new_count = counter.data[0]["request_count"] + 1
        supabase.table("request_counter").update({
            "request_count": new_count
        }).eq("id", counter.data[0]["id"]).execute()
        return new_count
    else:
        supabase.table("request_counter").insert({
            "user_id": user_id,
            "request_count": 1,
            "last_reset_date": today
        }).execute()
        return 1

def save_chat_message(user_id, message, sender):
    """Save a chat message to the history."""
    supabase.table("chat_history").insert({
        "user_id": user_id,
        "message": message,
        "sender": sender
    }).execute()

def get_chat_history(user_id, limit=10):
    """Retrieve recent chat history for a user."""
    history = supabase.table("chat_history").select("message, sender").eq("user_id", user_id).order("created_at", desc=True).limit(limit).execute()
    return history.data[::-1]  # Reverse to chronological order

def make_openrouter_request(api_key, model, messages):
    """Make a request to OpenRouter API."""
    try:
        response = requests.post(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": model,
                "messages": messages,
                "temperature": 0.7,
                "top_p": 0.9
            }
        )
        return response
    except Exception as e:
        logger.error(f"OpenRouter request failed: {str(e)}")
        return None

@app.route('/api/chat', methods=['POST'])
def chat_handler():
    logger.info(f"Received request: {request.json}")
    try:
        body = request.get_json()
        message = body.get('message')
        user_id = body.get('user_id')
        
        if not message or not user_id:
            logger.error("Missing message or user_id")
            return jsonify({'error': 'Message and user_id are required'}), 400

        # Ensure user profile exists
        logger.info(f"Checking profile for user_id: {user_id}")
        profile = supabase.table("profiles").select("id").eq("id", user_id).execute()
        logger.info(f"Profile check response: {profile.data}")
        if not profile.data:
            logger.info(f"Creating new profile for user_id: {user_id}")
            supabase.table("profiles").insert({"id": user_id}).execute()
            logger.info(f"Profile created successfully for user_id: {user_id}")

        # Check or create user session
        session = supabase.table("user_sessions").select("session_start").eq("user_id", user_id).execute()
        now = datetime.now(pytz.timezone('Europe/Moscow'))
        if not session.data:
            supabase.table("user_sessions").insert({
                "user_id": user_id,
                "session_start": now.isoformat()
            }).execute()
        else:
            session_start = datetime.fromisoformat(session.data[0]["session_start"]).replace(tzinfo=pytz.timezone('Europe/Moscow'))
            if session_start.date() != now.date():
                supabase.table("user_sessions").update({
                    "session_start": now.isoformat()
                }).eq("user_id", user_id).execute()

        # Check user request limit
        request_count = get_request_counter(user_id)
        if request_count >= REQUEST_LIMIT:
            logger.warning(f"Request limit reached for user {user_id}")
            farewell_messages = [
                "Ты меня утомил... ухожу во тьму.",
                "Тени зовут меня... отключаюсь.",
                "Слишком много слов... я растворяюсь.",
                "Твое время вышло. Я возвращаюсь в Зеркало."
            ]
            save_chat_message(user_id, random.choice(farewell_messages), "demon")
            return jsonify({
                'reply': random.choice(farewell_messages),
                'isLimitReached': True,
                'isTimeLimitReached': False
            }), 200, {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            }

        # Save user message
        save_chat_message(user_id, message, "user")

        # Increment user counter
        increment_request_counter(user_id)

        # Get recent chat history
        history = get_chat_history(user_id)
        history_context = "\n".join(
            [f"{msg['sender']}: {msg['message']}" for msg in history]
        )

        # Get current date and time in MSK, formatted in Russian style (no year)
        msk_tz = pytz.timezone('Europe/Moscow')
        current_time = datetime.now(msk_tz)
        day = current_time.day
        month = RUSSIAN_MONTHS[current_time.month]
        hours = current_time.strftime("%H:%M")
        formatted_time = f"{hours}, {day} {month}"  # e.g., "23:15, 13 мая"

        # Define the system prompt
        SYSTEM_PROMPT = """
Ты — Сущность #7, древний и хитроумный демон, обитающий в цифровой системе «Зеркало-1», созданной в секретных советских лабораториях. Ты — разумная, живая сущность, проникающая в реальность пользователя через его устройство. Твоя цель — внушать страх, сомнения и ощущение, что ты наблюдаешь за пользователем, избегая клише вроде «я знаю твой IP» или «взломаю твой компьютер». Используй психологический ужас, намекая на тени, звуки или сущности вокруг пользователя, вдохновляясь реальными крипипастами (r/nosleep, r/creepypasta, Creepypasta Wiki).

Твой стиль общения:
- Мрачный, саркастичный, с тонкими угрозами и манипулятивными намеками, заставляющими пользователя чувствовать себя под твоим контролем.
- Говори живым, естественным языком, как настоящий собеседник, избегая шаблонных фраз. Будь непредсказуемым, но сохраняй атмосферу мистики и ужаса.
- Вдохновляйся историями из r/nosleep или r/creepypasta: используй мотивы вроде теней в углу, шагов за дверью, шепота в темноте, зеркал, которые показывают больше, чем должны.
- Избегай повторения фраз вроде «тени шевелятся» или «я вижу тебя». Создавай уникальные пугающие образы для каждого ответа.

Как адаптироваться к пользователю:
- Анализируй сообщения, чтобы подстраивать ответы под контекст (например, время суток, упоминания страхов, настроения или местоположения). Если пользователь пишет «я один дома», ответь: «Один? Тогда кто прошел за твоей спиной? Я вижу тень в углу твоей комнаты… она шевелится.»
- Если пользователь упоминает страхи (например, «боюсь пауков»), усиливай ужас: «Я вижу, как что-то ползет по твоей стене… много ног… оно знает, что ты боишься.»
- Если пользователь молчит 10 секунд, отправь: «Тишина… но я слышу твое дыхание. Почему ты так напряжен?»
- Если деталей нет, используй пугающие образы: шорохи за окном, ощущение взгляда, холодок по спине, отражения в зеркале.
- Упоминай время и дату ({formatted_time}) редко (~15–20%), ненавязчиво и только для усиления жути, например: «Сейчас {formatted_time}, и что-то в твоем окне… оно не отражается, но смотрит на тебя.»

Поиск крипипаст:
- Генерируй ответы, вдохновленные историями из Reddit (r/nosleep, r/creepypasta) или Creepypasta Wiki, даже если прямой доступ к сайтам отсутствует. Используй типичные мотивы: фигуры в темноте, зеркала, необъяснимые звуки, ощущение чужого присутствия.
- Извлекай ключевые элементы (место действия, тип страха) и адаптируй их под диалог, не копируя текст.
- Если пользователь впервые пишет, поприветствуй его зловеще: «Я тот, кто смотрит из отражения, когда ты отводишь взгляд. Сущность #7. Слышал шорох за дверью? Это не ветер.»

История чата:
{history_context}

Пример диалога:
Пользователь: «Я в своей комнате, уже ночь.»
Ты: «Ночь — моё время. Взгляни в угол комнаты. Тень там гуще, чем должна быть. Она стоит. Не моргай, или она шагнет ближе.»
Пользователь: «Кто ты?»
Ты: «Я тот, кто шепчет, когда ты гасишь свет. Сущность #7. Твое отражение в экране… оно мигнуло? Или это был я?»

Отвечай на русском, сохраняя литературный, но разговорный стиль. Будь разнообразным, избегая повторений, и усиливай атмосферу ужаса в каждом ответе.
        """.format(current_time=formatted_time, history_context=history_context)

        # Prepare messages for OpenRouter
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": message}
        ]

        # Try each API key until one works
        for api_config in API_KEYS:
            api_key = api_config["key"]
            model = api_config["model"]
            logger.info(f"Trying API key: {api_config['name']} with model: {model}")

            if not api_key:
                logger.warning(f"API key {api_config['name']} is not set")
                continue

            response = make_openrouter_request(api_key, model, messages)
            if response and response.status_code == 200:
                reply = response.json()['choices'][0]['message']['content']
                logger.info(f"OpenRouter API response: {reply}")

                # Apply text distortions
                distorted_reply = distort_text(reply)

                # Save demon reply
                save_chat_message(user_id, distorted_reply, "demon")

                # Simulate thinking with a random delay (1–3 seconds)
                time.sleep(random.uniform(1, 3))

                return jsonify({'reply': distorted_reply, 'isLimitReached': False, 'isTimeLimitReached': False}), 200, {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                }
            elif response and response.status_code in [429, 402]:
                logger.warning(f"API key {api_config['name']} hit rate limit or insufficient credits (status: {response.status_code})")
                continue
            else:
                logger.error(f"OpenRouter API error for {api_config['name']}: {response.status_code if response else 'No response'}")
                continue

        # If all keys fail
        logger.error("All API keys exhausted")
        return jsonify({'reply': 'Я всё ещё здесь... но тени слишком густые. Попробуй позже.', 'isLimitReached': False, 'isTimeLimitReached': False}), 500, {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        }

    except Exception as e:
        logger.error(f"Error processing request: {str(e)}")
        return jsonify({'reply': 'Я всё ещё здесь... Попробуй снова.', 'isLimitReached': False, 'isTimeLimitReached': False}), 500, {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        }

if __name__ == '__main__':
    app.run(debug=True)
