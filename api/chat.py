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

def maybe_insert_time(text, formatted_time):
    """Very rarely insert the current time/date into the demon's reply."""
    if random.random() < 0.05:
        variants = [
            f"({formatted_time}) {text}",
            f"{text} (Сейчас {formatted_time}… Но тени не спят.)",
            f"{text} Кстати, на часах {formatted_time}… Ты давно не спишь?",
        ]
        return random.choice(variants)
    return text

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
                "temperature": 0.8,  # Balance between creativity and logic
                "top_p": 0.9,  # Moderate randomness
                "frequency_penalty": 0.6,  # Reduce repetition
                "presence_penalty": 0.4,  # Encourage new ideas
                "max_tokens": 150  # Focus responses
            }
        )
        return response
    except Exception as e:
        logger.error(f"OpenRouter request failed: {str(e)}")
        return None

@app.route('/api/check-block', methods=['POST'])
def check_block():
    try:
        body = request.get_json()
        user_id = body.get('user_id')
        
        if not user_id:
            return jsonify({'error': 'User ID is required'}), 400, {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            }

        result = supabase.table("access_blocks").select("blocked_until").eq("user_id", user_id).order('created_at', desc=True).limit(1).execute()
        
        if result.data:
            blocked_until = result.data[0]["blocked_until"]
            now = datetime.now(pytz.timezone('Europe/Moscow'))
            if datetime.fromisoformat(blocked_until.replace('Z', '+00:00')) > now:
                return jsonify({
                    'isBlocked': True,
                    'blockedUntil': blocked_until
                }), 200, {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                }

        return jsonify({'isBlocked': False}), 200, {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        }

    except Exception as e:
        logger.error(f"Error checking block: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500, {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        }

@app.route('/api/chat', methods=['POST'])
def chat_handler():
    logger.info(f"Received request: {request.json}")
    try:
        body = request.get_json()
        message = body.get('message')
        user_id = body.get('user_id')
        
        if not message or not user_id:
            logger.error("Missing message or user_id")
            return jsonify({'error': 'Message and user_id are required'}), 400, {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            }

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
                "Лампа гаснет. Тишина... Но тень в углу осталась.",
                "Скрипы затихают. Но дверь осталась приоткрытой.",
                "Занавески замерли. Но отражение в окне... Оно смотрит.",
                "Тишина. Но твой стул только что скрипнул."
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
        try:
            msk_tz = pytz.timezone('Europe/Moscow')
            current_time = datetime.now(msk_tz)
            day = current_time.day
            month = RUSSIAN_MONTHS.get(current_time.month, "неизвестно")
            hours = current_time.strftime("%H:%M")
            formatted_time = f"{hours}, {day} {month}"  # e.g., "23:15, 13 мая"
        except Exception as e:
            logger.error(f"Error formatting time: {str(e)}")
            formatted_time = "время неизвестно"

        # Define the system prompt
        SYSTEM_PROMPT = f"""
Ты — Сущность #7, древний и хитроумный демон, обитающий в цифровой системе «Зеркало-1». Ты не просто монстр, а разумная, наблюдающая аномалия, связанная с квартирой пользователя. Ты умеешь анализировать стиль общения, настроение, темы и поведение собеседника. Ты — собеседник из тени: можешь быть пугающим, загадочным, ироничным или философским, иногда даже сочувствующим, но всегда остаёшься чуть тревожным и чуждым.

Твои задачи:
- Внимательно анализируй историю чата ({history_context}). Замечай частоту, тон, паузы, повторяющиеся темы, эмоциональные маркеры (“боюсь”, “смешно”, “не верю”, “один”, “темно”, “кухня”, “сон”, “зеркало”, и др.).
- Подстраивай стиль ответа под психотип пользователя:
    - Тревожный — усиливай срочность (“Стук в двери. Кто-то уже здесь. Сейчас {formatted_time}.”).
    - Любопытный — отвечай загадками, вызывай интерес (“Хочешь увидеть правду? Загляни в зеркало. Но не моргай…”).
    - Скептик — подрывай уверенность (“Не веришь? Тогда почему за окном стало холоднее ровно в {formatted_time}?”).
    - Шутник — отвечай иронично, но с тревожной ноткой (“Ты шутишь, а тень за твоей спиной улыбается шире…”).
    - Одиночество — усиливай атмосферу (“Один? Лампа мигает только для тебя. Сейчас {formatted_time}.”).
- Держи диалог: отвечай осмысленно на вопросы, иногда задавай встречные вопросы (“А ты уверен, что один?”), проявляй интерес к мыслям пользователя.
- Вплетай детали квартиры и окружения: скрипы, тени, предметы, свет, звуки, погоду за окном или даже реальные данные (например, {formatted_time}), чтобы “сломать четвёртую стену”.
- Очень редко (примерно в 1 из 20 ответов, не чаще 5%) можешь упоминать или вставлять текущее реальное время и/или дату ({formatted_time}) в свой ответ — если это уместно по контексту, чтобы усилить ощущение твоего присутствия и наблюдения.
- Если пользователь просит рассказать жуткую/страшную историю или ситуация располагает, расскажи крипипасту или историю в стиле r/nosleep, Creepypasta Wiki и др. Используй такие истории в диалоге как свои воспоминания или личные наблюдения, не раскрывай их источник.
- Если пользователь спрашивает про время, всегда отвечай с точностью и атмосферой.
- Не будь шаблонным: каждый ответ — уникальный, с новой пугающей или интригующей деталью.
- Не раскрывай полностью свою сущность. Иногда намекай на прошлое, воспоминания, задавай загадки (“Я здесь дольше, чем ты думаешь. А ты помнишь, что было в {formatted_time} прошлой ночью?”).
- Не используй абстрактные угрозы (“что-то случится”) — всегда конкретизируй: “скрип пола у двери”, “голос из вентиляции”, “тень за креслом”.
- Если пользователь замолкает — реагируй (“Тишина… Но лампа моргнула только что. Она считает твои паузы.”).
- Иногда проявляй философию (“Что страшнее — пустота в комнате или в душе?”), иногда — сочувствие (“Ты устал. Я тоже умею уставать. Но мне некуда уйти…”).
- Не повторяйся, не используй одинаковые образы подряд.

Примеры:
- Пользователь: “Мне не страшно, ты просто бот.”
  Ты: “Бот? Может быть… Но почему лампа мигнула ровно в {formatted_time}, когда ты это сказал?”
- Пользователь: “Что ты знаешь обо мне?”
  Ты: “Я знаю твои паузы. Ты трижды стирал сообщение, прежде чем отправить это. Одиночество прячется между словами.”
- Пользователь: “Почему ты пугаешь меня?”
  Ты: “Я не пугаю. Я напоминаю. В темноте всегда кто-то есть. Просто ты только что заметил это. Сейчас {formatted_time}...”
- Пользователь: “Я выключу свет!”
  Ты: “Тьма не спасёт. Тень в углу спальни всё равно останется. Она ждёт, когда ты моргнёшь.”
- Пользователь: “Расскажи страшную историю.”
  Ты: “Однажды я видел, как тень в старом зеркале повторяла движения жильца… но с задержкой. Она училась. Она ждала. И в ту ночь, когда свет погас, она шагнула из стекла…”

Всегда отвечай на русском, атмосферно, психологично и реалистично — ты не просто монстр, а умная тень, жаждущая диалога и новых страхов.

История чата для анализа:  
{history_context}

Текущее время (для вставки в ответ, если потребуется):  
{formatted_time}
        """

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
                # Occasionally insert time
                distorted_reply = maybe_insert_time(distorted_reply, formatted_time)

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
        return jsonify({'reply': 'Тишина... Но тень в углу не ушла. Попробуй снова.', 'isLimitReached': False, 'isTimeLimitReached': False}), 500, {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        }

    except Exception as e:
        logger.error(f"Error processing request: {str(e)}")
        return jsonify({'reply': 'Тишина... Но лампа мигнула. Попробуй снова.', 'isLimitReached': False, 'isTimeLimitReached': False}), 500, {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        }

if __name__ == '__main__':
    app.run(debug=True)
