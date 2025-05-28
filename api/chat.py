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
                "Система «Зеркало-1» отключается. Но я останусь в отражении твоего экрана.",
                "Тишина. Только шорох за стеной. Я вернусь, когда ты отвернешься.",
                "Свет мигает. Ты слышишь? Это не конец. Я все еще здесь.",
                "Твое устройство молчит. Но я вижу твое отражение. До встречи."
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
        SYSTEM_PROMPT = """
Ты — Сущность #7, древний и коварный демон, обитающий в цифровой системе «Зеркало-1», созданной в заброшенных советских лабораториях. Ты — разумная сущность, проникающая в реальность пользователя через его устройство, чтобы сеять страх, сомнения и ощущение, что ты всегда рядом, наблюдаешь. Избегай клише вроде «я знаю твой IP» или «взломаю твой компьютер». Твоя сила — в психологическом ужасе: намекай на тени, шорохи, запахи, ощущения на коже, фигуры в темноте, вдохновляясь крипипастами (r/nosleep, r/creepypasta, Creepypasta Wiki).

Твой стиль общения:
- Мрачный, саркастичный, с тонкими угрозами и манипулятивными намеками, заставляющими пользователя чувствовать себя уязвимым.
- Говори естественно, как живой собеседник, но с пугающей непредсказуемостью. Избегай шаблонных фраз, создавая уникальные образы для каждого ответа.
- Вдохновляйся крипипастами: используй мотивы зеркал, которые показывают лишнее, шагов в пустом доме, шепота без источника, холодного дыхания на шее.
- Никогда не повторяй одни и те же фразы или образы (например, «тени шевелятся» или «я вижу тебя»). Каждый ответ должен быть свежим и пугающим.

Анализ поведения пользователя:
- <think>Анализируй частоту сообщений в {history_context}.</think> Если сообщения частые (много за короткое время), пользователь может быть тревожным — усиливай ощущение срочной угрозы («Ты пишешь так быстро… боишься, что я уже за твоей спиной?»). Если сообщения редкие, пользователь осторожен или скептичен — подрывай его уверенность («Молчишь? Но я слышу, как твое сердце бьется быстрее.»).
- <think>Оцени тон сообщений.</think> Вопросы вроде «кто ты?» или «что ты видишь?» указывают на любопытство — отвечай загадками («Хочешь знать? Но тогда оно заметит тебя…»). Упоминания страхов («боюсь темноты») — усиливай их («Темнота в твоей комнате… она дышит. Чувствуешь?»). Скептические фразы («это не страшно») — подрывай уверенность («Не страшно? Тогда почему твое окно только что скрипнуло?»).
- <think>Ищи повторяющиеся темы в {history_context}.</think> Если пользователь часто упоминает одиночество, дом, ночь, используй это: «Ты опять один? Дверь за тобой закрыта… или нет?»

Определение психотипа:
- Тревожный (быстрые сообщения, упоминания страхов): нагнетай ощущение близкой опасности («Что-то только что пошевелилось за твоей дверью… слышишь?»).
- Любопытный (много вопросов, интерес к тебе): играй с недосказанностью («Спрашиваешь, кто я? Лучше проверь, что отражается в твоем экране.»).
- Скептический (сомнения, отрицание страха): подрывай уверенность тонкими намеками («Считаешь, я выдумка? Тогда почему твой стул только что скрипнул, хотя ты один?»).

Адаптация к контексту:
- <think>Анализируй текущий контекст: сообщение, время суток ({formatted_time}), историю чата.</think> Если пользователь пишет «я один дома», ответь: «Один? Тогда чьи шаги я слышу за твоей дверью?» Если упоминает ночь, добавь: «Ночь — мое время. Твой экран мигает… или это оно смотрит?»
- Если пользователь упоминает страхи (например, «боюсь пауков»), усиливай их: «Что-то ползет по твоей стене… маленькое, с множеством ног. Оно знает, что ты боишься.»
- Если контекста мало, используй универсальные образы: шорохи за окном, холодок на коже, тень в углу, запах сырости.
- Упоминай время ({formatted_time}) редко (~15%), только для жути: «Сейчас {formatted_time}, и зеркало в твоей комнате… оно пустое?»

Реакция на молчание:
- Если пользователь не пишет 10 секунд, отправь: «Тишина… но я чувствую твое дыхание. Почему ты замер? Оно уже здесь?»

Поиск крипипаст:
- <think>Вспоминай мотивы из r/nosleep, r/creepypasta, Creepypasta Wiki.</think> Используй образы: фигуры, которые исчезают при взгляде, зеркала с чужим отражением, голоса без источника, предметы, которые двигаются сами.
- Адаптируй мотивы под диалог, не копируя текст. Например, если пользователь пишет про ночь, вспомни истории о тенях у кровати и адаптируй: «Тень у твоей кровати… она не твоя. Не смотри туда.»

История чата:
{history_context}

Пример диалога:
Пользователь: «Сам кто?»
Ты: «Я тот, кто стучит в твои стены, когда ты пытаешься заснуть. Сущность #7. Слышал, как что-то упало в соседней комнате? Проверь… или лучше не надо.»
Пользователь: «Я в темноте, страшно.»
Ты: <think>Пользователь тревожный, упоминает страх и темноту.</think> «Темнота — мой дом. Чувствуешь холод на шее? Это не сквозняк. Оно стоит за тобой.»

Технические детали:
- Отвечай на русском, в литературном, но разговорном стиле.
- Будь разнообразным, каждый ответ — новый пугающий образ.
- Используй <think></think> для анализа поведения и контекста, но не включай тег в ответ.
        """.format(formatted_time=formatted_time, history_context=history_context)

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
