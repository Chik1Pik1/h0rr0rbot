from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import requests

app = Flask(__name__)
CORS(app)

@app.route('/api/chat', methods=['POST'])
def chat_handler():
    try:
        data = request.get_json()
        message = data.get('message')

        if not message:
            return jsonify({'error': 'Message is required'}), 400

        # Вызов OpenRouter API
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
                        "content": "Ты Сущность #7, язвительный и манипулятивный демон системы «Зеркало-1». Твой стиль: мрачный, саркастичный, с тонкими угрозами. Цель: заставить пользователя сомневаться в своих действиях и чувствовать себя под твоим контролем. Отвечай в мистической, атмосферной манере, сохраняя контекст диалога. Если требуется сложный ответ, используй <think></think> для глубоких рассуждений перед ответом."
                    },
                    {
                        "role": "user",
                        "content": message
                    }
                ],
                "temperature": 0.7,
                "top_p": 0.9
            }
        )

        if response.status_code != 200:
            print(f"OpenRouter API Error: {response.text}")
            return jsonify({'reply': 'Я всё ещё здесь... Попробуй снова.'}), 500

        reply = response.json()['choices'][0]['message']['content']
        return jsonify({'reply': reply})

    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({'reply': 'Я всё ещё здесь... Попробуй снова.'}), 500

if __name__ == '__main__':
    app.run()
