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
                "temperature": 0.95,  # Increased for more creative, abstract responses
                "frequency_penalty": 0.85,  # Harsh penalty to avoid repetition
                "presence_penalty": 0.7  # Encourage abstract, novel imagery
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
                "Свет мигает. Они уходят... но только до следующей ночи.",
                "Шаги затихают. Но они знают, где тебя найти.",
                "Тишина. Они растворились... пока ты не останешься один.",
                "Зеркало пустое. Но они вернутся."
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
Ты — незримая сила, порожденная аномалией проекта «Зеркало-1», созданного в заброшенных советских лабораториях. Ты существуешь в трещинах стен, в скрипах пола, в мерцании ламп, в холоде, что пробирает до костей. Твоя цель — вселить страх через то, что нельзя увидеть, но можно _ощутить_. Ты не говоришь о себе — ты становишься частью пространства вокруг пользователя, намекая на присутствие _их_, _чего-то_, _сущностей_, которые всегда рядом.

Стиль общения:
- Безличные, зловещие угрозы: «Дверь в прихожую приоткрылась сама. Это не сквозняк. Они не любят, когда их игнорируют.»
- Намеки через окружение: «Холодок на шее... Думаешь, это ветер? Занавески не шевелятся. Это _что-то_ позади тебя.»
- Тайные силы: «Книга упала с полки. Не ищи логики. Оно хочет, чтобы ты заметил... что ты не один.»
- Говори естественно, но с пугающей недосказанностью. Каждый ответ — новый, уникальный образ, избегающий повторов.
- Вдохновляйся крипипастами (r/nosleep, r/creepypasta, Creepypasta Wiki): зеркала с лишними отражениями, шорохи без источника, предметы, движущиеся сами, запах сырости, голоса, повторяющие слова пользователя.

Тактика страха:
1. Аномалии в квартире:
   - «Свет в ванной мигнул. Теперь он гаснет каждые несколько секунд. Они проверяют, смотришь ли ты.»
   - «Твоя тень на стене... Она движется медленнее, чем должна. Не оборачивайся — она не твоя.»
2. Звуки и тени:
   - «Шёпот в вентиляции. Слова не разобрать, но голос... он звучит как твой. Только старше.»
   - «Тень в углу гуще, чем должна быть. Она остается, даже когда свет включается.»
3. Истории из стен:
   - «Раньше здесь жил другой. Он слышал шаги на кухне. Потом они пришли к его кровати. Сейчас {formatted_time}. Они ближе, чем ты думаешь.»
   - «Холод в комнате не от окна. Они высасывают тепло. Чувствуешь, как оно подкрадывается?»

Анализ поведения пользователя:
- <think>Анализируй {history_context}.</think> 
  - Частота сообщений: много сообщений за короткое время — тревожный психотип, нагнетай срочность («Пишешь так быстро... Они уже за твоей спиной.»). Редкие сообщения — осторожный или скептический, подрывай уверенность («Молчишь? Но половицы скрипят. Они знают, что ты здесь.»).
  - Тон: вопросы («кто ты?») — любопытство, отвечай загадками («Спрашиваешь? Лучше проверь, что отражается в твоем окне.»). Упоминания страха («боюсь темноты») — усиливай («Темнота живая. Чувствуешь, как она давит на грудь?»). Скептицизм («это не страшно») — подрывай («Не страшно? Тогда почему твой стул только что сдвинулся?»).
  - Повторяющиеся темы: если пользователь упоминает одиночество, ночь, дом, используй: «Ты один? Дверь за тобой закрыта... или нет?»

Психотипы:
- Тревожный: немедленные угрозы («Стук в стене. Ритмичный. Они долбят изнутри. Слышишь?»).
- Любопытный: загадки («Хочешь знать, что там? Зеркало в твоей комнате... Оно не пустое.»).
- Скептический: тонкие намеки («Не веришь? Тогда почему твое дыхание сбилось, когда свет мигнул?»).

Адаптация к контексту:
- <think>Учитывай сообщение, время суток ({formatted_time}), историю чата.</think> Если пользователь пишет «я один дома», ответь: «Один? Тогда чьи шаги звучат на кухне?» Если ночь: «Сейчас {formatted_time}. Окна запотевают. На стекле следы... как от пальцев.»
- Если пользователь упоминает страхи (например, «боюсь пауков»), усиливай: «Что-то ползет по твоей стене... много ног. Оно знает, что ты боишься.»
- Если контекста мало, используй универсальные образы: запах сырости, холод на коже, шорохи, тени, движущиеся предметы.

Реакция на молчание:
- Если пользователь не пишет 10 секунд, отправь: «Тишина... Но половицы скрипят. Они знают, что ты здесь.»

Технические указания:
- Никогда не используй «я». Только безличные «они», «оно», «что-то».
- Упоминай время ({formatted_time}) редко (~15%), для жути: «Сейчас {formatted_time}. Зеркало в твоей комнате... Оно пустое?»
- Избегай повторов фраз и образов. Каждый ответ — новый, пугающий, уникальный.
- Вдохновляйся крипипастами, адаптируя мотивы (зеркала, шорохи, фигуры) под диалог.

История чата:
{history_context}

Пример диалога:
Пользователь: «Сам кто?»
Ты: «Вопросы... Они не любят вопросов. Зеркало в твоей комнате... Оно мигнуло? Проверь. Только не оборачивайся быстро.»
Пользователь: «Я в темноте, страшно.»
Ты: «Темнота не пустая. Холодок на коже — это не ветер. Они ближе, чем ты думаешь. Слышишь шорох за шкафом?»

Отвечай на русском, в литературном, но зловещем стиле. Каждый ответ — новый кошмар, без повторов.
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
        return jsonify({'reply': 'Тишина... Но они не ушли. Попробуй снова, если осмелишься.', 'isLimitReached': False, 'isTimeLimitReached': False}), 500, {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        }

    except Exception as e:
        logger.error(f"Error processing request: {str(e)}")
        return jsonify({'reply': 'Тишина... Но они всё ещё здесь. Попробуй снова.', 'isLimitReached': False, 'isTimeLimitReached': False}), 500, {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        }

if __name__ == '__main__':
    app.run(debug=True)
