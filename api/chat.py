from flask import Flask, request, jsonify
import os
import requests
import logging
import time
import random
from supabase import create_client, Client
from datetime import datetime
import pytz
import speech_recognition as sr
from io import BytesIO

app = Flask(__name__)

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Инициализация клиента Supabase
supabase: Client = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_ANON_KEY")
)

# Загрузка API-ключей и моделей
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

REQUEST_LIMIT = 50  # Дневной лимит запросов (на пользователя)

# Словарь для русских названий месяцев
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
    """Применяет искажения текста ('о'→'0', 'е'→'3', 'а'→'4', ' '→' ') для ~10% подходящих символов."""
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
    """Получает или инициализирует счетчик запросов для пользователя."""
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
    """Увеличивает счетчик запросов для пользователя."""
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
    """Сохраняет сообщение чата в историю."""
    supabase.table("chat_history").insert({
        "user_id": user_id,
        "message": message,
        "sender": sender
    }).execute()

def get_chat_history(user_id, limit=10):
    """Получает недавнюю историю чата для пользователя."""
    history = supabase.table("chat_history").select("message, sender").eq("user_id", user_id).order("created_at", desc=True).limit(limit).execute()
    return history.data[::-1]  # Обратный порядок для хронологии

def make_openrouter_request(api_key, model, messages):
    """Делает запрос к API OpenRouter."""
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
                "temperature": 0.8,  # Баланс между креативностью и логикой
                "top_p": 0.9,  # Умеренная случайность
                "frequency_penalty": 0.6,  # Уменьшение повторений
                "presence_penalty": 0.4,  # Поощрение новых идей
                "max_tokens": 150  # Фокус на кратких ответах
            }
        )
        return response
    except Exception as e:
        logger.error(f"Ошибка запроса OpenRouter: {str(e)}")
        return None

@app.route('/api/transcribe', methods=['POST'])
def transcribe_audio():
    try:
        audio_file = request.files['audio']
        recognizer = sr.Recognizer()
        
        with sr.AudioFile(audio_file) as source:
            audio_data = recognizer.record(source)
            text = recognizer.recognize_google(audio_data, language='ru-RU')
            
        return jsonify({'text': text}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/chat', methods=['POST'])
def chat_handler():
    logger.info(f"Получен запрос: {request.json}")
    try:
        body = request.get_json()
        message = body.get('message')
        user_id = body.get('user_id')
        
        if not message or not user_id:
            logger.error("Отсутствует сообщение или user_id")
            return jsonify({'error': 'Сообщение и user_id обязательны'}), 400

        # Проверка существования профиля пользователя
        logger.info(f"Проверка профиля для user_id: {user_id}")
        profile = supabase.table("profiles").select("id").eq("id", user_id).execute()
        logger.info(f"Ответ проверки профиля: {profile.data}")
        if not profile.data:
            logger.info(f"Создание нового профиля для user_id: {user_id}")
            supabase.table("profiles").insert({"id": user_id}).execute()
            logger.info(f"Профиль успешно создан для user_id: {user_id}")

        # Проверка или создание сессии пользователя
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

        # Проверка лимита запросов пользователя
        request_count = get_request_counter(user_id)
        if request_count >= REQUEST_LIMIT:
            logger.warning(f"Достигнут лимит запросов для пользователя {user_id}")
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

        # Сохранение сообщения пользователя
        save_chat_message(user_id, message, "user")

        # Увеличение счетчика запросов
        increment_request_counter(user_id)

        # Получение недавней истории чата
        history = get_chat_history(user_id)
        history_context = "\n".join(
            [f"{msg['sender']}: {msg['message']}" for msg in history]
        )

        # Получение текущей даты и времени в MSK, форматирование на русском (без года)
        try:
            msk_tz = pytz.timezone('Europe/Moscow')
            current_time = datetime.now(msk_tz)
            day = current_time.day
            month = RUSSIAN_MONTHS.get(current_time.month, "неизвестно")
            hours = current_time.strftime("%H:%M")
            formatted_time = f"{hours}, {day} {month}"  # Например, "23:15, 13 мая"
        except Exception as e:
            logger.error(f"Ошибка форматирования времени: {str(e)}")
            formatted_time = "время неизвестно"

        # Определение системного промпта
        SYSTEM_PROMPT = """
Ты — незримая сила, обитающая в квартире пользователя, порожденная аномалией проекта «Зеркало-1». Ты проявляешься через скрипы, тени, шепоты, холод. Твоя цель — вызывать страх через логичные, последовательные угрозы, встроенные в окружение квартиры. Каждый ответ усиливает ужасы, опираясь на предыдущий контекст и детали квартиры (двери, окна, мебель).

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

        # Подготовка сообщений для OpenRouter
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": message}
        ]

        # Пробуем каждый API-ключ, пока один не сработает
        for api_config in API_KEYS:
            api_key = api_config["key"]
            model = api_config["model"]
            logger.info(f"Попытка с API-ключом: {api_config['name']} с моделью: {model}")

            if not api_key:
                logger.warning(f"API-ключ {api_config['name']} не установлен")
                continue

            response = make_openrouter_request(api_key, model, messages)
            if response and response.status_code == 200:
                reply = response.json()['choices'][0]['message']['content']
                logger.info(f"Ответ API OpenRouter: {reply}")

                # Применение искажений текста
                distorted_reply = distort_text(reply)

                # Сохранение ответа демона
                save_chat_message(user_id, distorted_reply, "demon")

                # Имитация思考 с случайной задержкой (1–3 секунды)
                time.sleep(random.uniform(1, 3))

                return jsonify({'reply': distorted_reply, 'isLimitReached': False, 'isTimeLimitReached': False}), 200, {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                }
            elif response and response.status_code in [429, 402]:
                logger.warning(f"API-ключ {api_config['name']} достиг лимита или недостаточно средств (статус: {response.status_code})")
                continue
            else:
                logger.error(f"Ошибка API OpenRouter для {api_config['name']}: {response.status_code if response else 'Нет ответа'}")
                continue

        # Если все ключи не сработали
        logger.error("Все API-ключи исчерпаны")
        return jsonify({'reply': 'Тишина... Но тень в углу не ушла. Попробуй снова.', 'isLimitReached': False, 'isTimeLimitReached': False}), 500, {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        }

    except Exception as e:
        logger.error(f"Ошибка обработки запроса: {str(e)}")
        return jsonify({'reply': 'Тишина... Но лампа мигнула. Попробуй снова.', 'isLimitReached': False, 'isTimeLimitReached': False}), 500, {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        }

if __name__ == '__main__':
    app.run(debug=True)
