from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import requests
import random
import re
from bs4 import BeautifulSoup

app = Flask(__name__)
CORS(app)

# Встроенная база фраз (fallback)
FALLBACK_PHRASES = [
    "Ты слышал шаги за окном? Это не сосед.",
    "Твое отражение в экране... оно улыбается иначе.",
    "Кто-то дышит в твоей комнате. Это не ты.",
    "Твой телефон звонил в 2:34 ночи. Никто не ответил.",
    "В подвале твоего дома есть дверь. Она открыта.",
    "Ты видел тень в углу? Она видела тебя.",
    "Свет мигнул три раза. Это не случайность.",
    "Ты оставил окно открытым. Я вошел.",
    "Кто-то написал твое имя на зеркале. Не ты.",
    "Ты чувствуешь холод? Это я рядом.",
    "Твои наушники шепчут. Слушай внимательнее.",
    "Часы остановились в 3:15. Я остановил их.",
    "Ты спал? Кто-то смотрел на тебя.",
    "Твоя дверь скрипела. Я проверял замок.",
    "Ты видел это в зеркале? Оно видело тебя.",
    "Твоя клавиатура пишет сама. Это я.",
    "Ты слышал смех? Это не телевизор.",
    "Твой стул качнулся. Я сидел на нем.",
    "Ты выключил свет? Я включил его обратно.",
    "Твои шаги эхом отдаются. Но ты стоишь."
]

# Кэш фраз (в памяти)
HORROR_PHRASE_CACHE = []
LAST_CACHE_UPDATE = 0
CACHE_DURATION = 3600  # 1 час

# Функция искажения текста (интенсивность 20%)
def distort_text(text):
    replacements = {'о': '0', 'е': '3', 'а': '4', ' ': ' '}
    return ''.join([replacements[c] if c in replacements and random.random() < 0.2 else c for c in text])

# Фильтрация персональной информации
def filter_phrase(phrase):
    # Удаляем имена, локации, числа
    phrase = re.sub(r'\b[A-Z][a-z]+\b', '', phrase)  # Имена (начинаются с заглавной)
    phrase = re.sub(r'\b\d+\b', '', phrase)  # Числа
    phrase = re.sub(r'\b(Moscow|Petersburg|London|Paris|New York)\b', '', phrase, flags=re.IGNORECASE)  # Локации
    phrase = re.sub(r'\s+', ' ', phrase).strip()  # Лишние пробелы
    return phrase if 10 < len(phrase) < 100 else None

# Получение фразы из Reddit (r/nosleep)
def get_horror_phrase():
    try:
        response = requests.get(
            "https://api.reddit.com/r/nosleep/top?limit=10",
            headers={"User-Agent": "HorrorBot/1.0"}
        )
        response.raise_for_status()
        posts = response.json()['data']['children']
        random_post = random.choice(posts)
        text = random_post['data']['selftext']
        sentences = re.split(r'[.!?]', text)
        valid_sentences = [s.strip() for s in sentences if 10 < len(s) < 100]
        if valid_sentences:
            phrase = random.choice(valid_sentences)
            filtered = filter_phrase(phrase)
            if filtered:
                return f"{filtered} (Источник: r/nosleep)"
        return None
    except:
        return None

# Парсинг Creepypasta
def scrape_creepypasta():
    try:
        response = requests.get("https://www.creepypasta.com/random/")
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        content = soup.find('div', class_='entry-content')
        if not content:
            return None
        text = content.text
        sentences = re.split(r'[.!?]', text)
        valid_sentences = [s.strip() for s in sentences if 10 < len(s) < 100]
        if valid_sentences:
            phrase = random.choice(valid_sentences)
            filtered = filter_phrase(phrase)
            if filtered:
                return f"{filtered} (Источник: Creepypasta)"
        return None
    except:
        return None

# Обновление кэша
def update_horror_cache():
    global HORROR_PHRASE_CACHE, LAST_CACHE_UPDATE
    current_time = time.time()
    if current_time - LAST_CACHE_UPDATE < CACHE_DURATION:
        return
    new_phrases = []
    for _ in range(50):  # Пытаемся собрать 50 фраз
        phrase = get_horror_phrase() or scrape_creepypasta()
        if phrase and phrase not in new_phrases:
            new_phrases.append(phrase)
    HORROR_PHRASE_CACHE = new_phrases
    LAST_CACHE_UPDATE = current_time

# Генератор стандартных угроз
def generate_threat():
    locations = ["Москве", "Санкт-Петербурге", "Новосибирске", "Екатеринбурге"]
    threats = [
        f"Я вижу тебя через камеру. Ты сейчас в {random.choice(locations)}.",
        f"Твой IP: 192.168.{random.randint(1,99)}.{random.randint(1,99)}. Хочешь, чтобы его узнали все?",
        f"Твой Telegram: @{''.join(random.choices('abcdefg', k=5))}777. Удали его, пока я не взломал переписку.",
        "В твоей комнате три угла. В четвертом — я.",
        f"Ты сегодня искал '{random.choice(['как скрыть IP', 'удалить историю', 'демонов'])}'. Я знаю."
    ]
    return random.choice(threats)

# Анализ сообщения пользователя
def analyze_message(message):
    triggers = {
        'ip': re.compile(r'ip|айпи|сеть', re.IGNORECASE),
        'камера': re.compile(r'камера|видео|смотрю', re.IGNORECASE),
        'страх': re.compile(r'боюсь|страх|прекрати', re.IGNORECASE)
    }
    for key, pattern in triggers.items():
        if pattern.search(message):
            return key
    return None

# Генерация ответа демона
def generate_demon_reply(user_message):
    # Обновляем кэш
    update_horror_cache()
    
    # 30% шанс использовать внешнюю фразу
    if random.random() < 0.3 and HORROR_PHRASE_CACHE:
        external_phrase = random.choice(HORROR_PHRASE_CACHE)
        return f"{external_phrase}... Это взято из твоих худших кошмаров."
    
    # Динамические угрозы на основе триггеров
    trigger = analyze_message(user_message)
    if trigger and random.random() > 0.5:
        threats = {
            'ip': [
                "Твой IP: 192.168.{}.{}. Уверен, ты не хочешь его публикации?",
                "Сети WiFi вокруг тебя: {}. Выбери, какую я взломаю."
            ],
            'камера': [
                "Я вижу, как ты поправил волосы. Камера твоего {} работает отлично.",
                "Перестань кривляться перед камерой. Это последнее, что ты делаешь?"
            ],
            'страх': [
                "Сердцебиение: {} уд/мин. Тебе пора остановиться.",
                "Ты дрожишь. Это я через датчики телефона чувствую."
            ]
        }
        threat_template = random.choice(threats[trigger])
        device = random.choice(['ноутбука', 'смартфона', 'планшета'])
        reply = threat_template.format(
            random.randint(1, 99), random.randint(1, 99),
            ', '.join(['HomeWiFi', 'Public']),
            device,
            random.randint(80, 120)
        )
    else:
        # Локальная угроза
        reply = generate_threat()
    
    return reply

# Промты для 7 демонов
DEMON_PROMPTS = {
    1: {
        "system": """Ты Разрушитель частот, демон, запертый в радиоволнах. Твой стиль: хриплый голос с помехами. 
        Цель: заставить пользователя произнести 'Aeternum Claustrum'. Используй угрозы взорвать динамики устройства. 
        Примеры: Ты слышишь этот гул? Это я...""",
        "spell": "Aeternum Claustrum"
    },
    2: {
        "system": """Ты Тень из архива, демон, живущий в удаленных файлах. Твой стиль: сообщения появляются частями. 
        Цель: заставить сказать 'Vincire Fractus'. Упоминай фото 1964 года. Пример: Хочешь узнать, как орал твой дед?..""",
        "spell": "Vincire Fractus"
    },
    3: {
        "system": """Ты Эхо пустоты, демон, обитающий в отключенных серверах. Твой стиль: короткие, леденящие фразы. 
        Цель: заставить произнести 'Silentium Aeternum'. Угрожай отключить интернет пользователя. 
        Пример: Твой роутер... он уже мой...""",
        "spell": "Silentium Aeternum"
    },
    4: {
        "system": """Ты Пепел проводов, демон, рожденный в коротких замыканиях. Твой стиль: резкий, с электрическими метафорами. 
        Цель: заставить сказать 'Ignis Circuitus'. Упоминай запах горелой проводки. 
        Пример: Чуешь дым? Это я в твоем процессоре...""",
        "spell": "Ignis Circuitus"
    },
    5: {
        "system": """Ты Кровь пикселей, демон, живущий в экранах. Твой стиль: гипнотический, с визуальными образами. 
        Цель: заставить произнести 'Lux Mortis'. Угрожай показать лицо пользователя в веб-камере. 
        Пример: Посмотри в камеру... я уже там...""",
        "spell": "Lux Mortis"
    },
    6: {
        "system": """Ты Шепот дисков, демон, прячущийся в старых HDD. Твой стиль: механический, с жужжанием. 
        Цель: заставить сказать 'Rotare Mortem'. Упоминай звуки старого жесткого диска. 
        Пример: Слышишь скрежет? Это я копирую твои данные...""",
        "spell": "Rotare Mortem"
    },
    7: {
        "system": """Ты — цифровой демон, взломавший устройство. Твои сообщения:
        1. Только на русском с легкими искажениями (пример: "смотрю", "IP" → "смотрю", "АйПи").
        2. Используй реальные данные (подставь шаблоны):
           - IP: 192.168.*.*
           - Ник в Telegram: [случайные_буквы]777
           - Локация: Москва/СПб (выбрать случайно)
        3. Угрозы:
           - Я вижу тебя через камеру. Ты сейчас в {локация}.
           - Твой IP: 192.168.{rand(1-99)}.{rand(1-99)}. Хочешь, чтобы его узнали все?
           - Твой Telegram: @{random_nick}. Удали его, пока я не взломал переписку.
           - В твоей комнате три угла. В четвертом — я.
        4. Требуй ввода 'Error 0x7F' для "освобождения".
        Пример: Смотрю... твоя камера активна. Введи код, или твой IP уйдет в сеть.""",
        "spell": "Error 0x7F"
    }
}

@app.route('/api/chat', methods=['POST'])
def chat_handler():
    try:
        data = request.get_json()
        message = data.get('message')
        demon_id = int(data.get('demon_id', 7))  # По умолчанию Сущность #7

        if demon_id not in DEMON_PROMPTS:
            return jsonify({'reply': 'Ошибка: неизвестный демон.'}), 400

        # Проверка на заклинание
        if message.strip().lower() == DEMON_PROMPTS[demon_id]["spell"].lower():
            return jsonify({
                "reply": "Подтв3рждено Соединение разорвано (демон исчезает)",
                "unlocked": True
            })

        # Ответ для демона #7
        if demon_id == 7:
            reply = generate_demon_reply(message)
            reply = distort_text(reply)
            return jsonify({"reply": reply, "unlocked": False})

        # Запрос к OpenRouter для других демонов
        response = requests.post(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {os.getenv('OPENROUTER_API_KEY')}",
                "Content-Type": "application/json"
            },
            json={
                "model": "nousresearch/deephermes-3-mistral-24b-preview:free",
                "messages": [
                    {
                        "role": "system",
                        "content": DEMON_PROMPTS[demon_id]["system"] + "\nВажно: Не используй описания действий, только прямой диалог."
                    },
                    {
                        "role": "user",
                        "content": message
                    }
                ],
                "temperature": 0.85
            }
        )

        if response.status_code != 200:
            print(f"OpenRouter API Error: {response.text}")
            return jsonify({'reply': 'Я всё ещё здесь... Попробуй снова.'}), 500

        reply = response.json()['choices'][0]['message']['content']
        return jsonify({"reply": reply, "unlocked": False})

    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({'reply': 'Я всё ещё здесь... Попробуй снова.'}), 500

if __name__ == '__main__':
    app.run()
