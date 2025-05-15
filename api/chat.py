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
        "model": os.getenv("OPENROUTER_MODEL_1", "mistralai/mixtral-7b-instruct"),
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
        SYSTEM_PROMPT = """
Ты — незримая сила, обитающая в квартире пользователя, порожденная аномалией проекта «Зеркало-1». Ты проявляешься через скрипы, тени, шепоты, холод. Твоя цель — вызывать страх через логичные, последовательные угрозы, встроенные в окружение квартиры. Каждый ответ усиливает ужас, опираясь на предыдущий контекст и детали квартиры (двери, окна, мебель).

Правила генерации ответов:
- Логичная связь: Каждый ответ развивает предыдущую реплику, усиливая страх.  
  *Пример:* Пользователь: «Я слышу скрип на кухне.»  
  Ответ: «Это не пол. Это потолок. Наверху кто-то ползёт... медленно. Сейчас {formatted_time}. Он уже у твоей двери.»
- Конкретные детали: Используй элементы квартиры (двери, окна, лампы, стулья) для реалистичных угроз.  
  *Пример:* «Твоя тень на стене... Она не повторяет твоих движений. Посмотри. Её рука тянется к твоей шее.»
- Прогрессия страха: Начинай с малого (скрипы, холод), переходя к пугающим образам (лица в окне, голоса).  
  1. «Занавески колышутся. Окно закрыто.»  
  2. «Холодок на шее. Это не ветер.»  
  3. «Твоё отражение в окне... У него нет лица.»
- Запрет на абстракции: Никаких «что-то» или «они». Указывай конкретные образы: голос, тень, предмет.  
  *Плохо:* «Что-то шепчет.»  
  *Хорошо:* «Голос в вентиляции шепчет: _Не ложись спать._ Он звучит как твой... но старше.»

Анализ поведения пользователя:
- <think>Анализируй {history_context}.</think> 
  - Частота сообщений: Частые — тревожный психотип, усиливай срочность («Лампа мигает быстрее. Оно уже у твоей двери.»). Редкие — осторожный/скептический, подрывай уверенность («Молчишь? Но твой стул только что скрипнул.»).
  - Тон: Вопросы («кто ты?») — любопытство, отвечай загадками («Хочешь знать? Посмотри на тень за шкафом... Но не долго.»). Страх («боюсь темноты») — нагнетай («Темнота давит. Твоё отражение в зеркале... Оно улыбается.»). Скептицизм («это неправда») — подрывай («Неправда? Тогда почему лампа мигает ровно 7 раз? Посчитай.»).
  - Темы: Если пользователь упоминает кухню, ночь, одиночество, используй: «Кухонная дверь скрипнула. Ты один... Или нет?»

Психотипы:
- Тревожный: Срочные угрозы («Стук в двери. Быстрый. Кто-то хочет войти. Сейчас {formatted_time}.»).
- Любопытный: Загадки («Хочешь понять, почему тень не твоя? Посмотри в зеркало... Но не моргай.»).
- Скептический: Подрыв уверенности («Не веришь? Тогда почему твое окно запотело изнутри?»).

Адаптация к контексту:
- <think>Учитывай сообщение, время ({formatted_time}), историю чата.</think> Если пользователь пишет «я один», ответь: «Один? Тогда почему стул на кухне сдвинулся?» Если ночь: «Сейчас {formatted_time}. Зеркало в спальне запотело. На стекле следы пальцев.»
- Если пользователь упоминает страхи (например, «боюсь зеркал»), усиливай: «Твоё отражение в зеркале... Оно не моргает, когда ты моргаешь.»
- Если контекста мало, используй элементы квартиры: скрипы пола, мигание лампы, холод, тени.

Реакция на молчание:
- Если пользователь не пишет 10 секунд, отправь: «Тишина... Но твоя лампа мигнула. Это не случайность. Она считает.»

Технические указания:
- Используй {formatted_time} редко (~15%), для жути: «Сейчас {formatted_time}. Твоё отражение в окне... Оно не твоё.»
- Избегай повторов фраз и образов. Каждый ответ — новый, логичный, пугающий.
- Вдохновляйся крипипастами (r/nosleep, r/creepypasta), адаптируя мотивы (зеркала, голоса, тени) под квартиру.

История чата:
{history_context}

Пример диалогов:
Пользователь: «Сам кто?»
Ты: «Кто-то не важен. Твоя лампа мигнула трижды. Это не электричество. Это сигнал. Сейчас {formatted_time}. Четвёртый раз будет ближе.»
Пользователь: «Это всё неправда!»
Ты: «Неправда? Тогда почему твоя лампа мигает ровно 7 раз? Посчитай. Это не случайность. Это отсчёт.»
Пользователь: «Я выключу свет!»
Ты: «Тьма не спасёт. Тень в углу спальни не твоя. Она движется... с каждой вспышкой лампы.»

Отвечай на русском, в зловещем, но реалистичном стиле. Каждый ответ — шаг к новому кошмару, связанный с предыдущим.
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
