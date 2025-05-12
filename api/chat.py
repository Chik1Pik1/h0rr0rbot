import json
import os
import requests

def handler(event, context):
    try:
        # Проверяем метод запроса
        if event.get('httpMethod') != 'POST':
            return {
                'statusCode': 405,
                'body': json.dumps({'error': 'Only POST requests are allowed'}),
                'headers': {'Content-Type': 'application/json'}
            }

        # Получаем тело запроса
        body = json.loads(event.get('body', '{}'))
        message = body.get('message')
        if not message:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'Message is required'}),
                'headers': {'Content-Type': 'application/json'}
            }

        # Вызов OpenRouter API
        response = requests.post(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {os.getenv('OPENROUTER_API_KEY')}",
                "Content-Type": "application/json"
            },
            data=json.dumps({
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
            })
        )

        if response.status_code != 200:
            print(f"OpenRouter API Error: {response.text}")
            return {
                'statusCode': 500,
                'body': json.dumps({'reply': 'Я всё ещё здесь... Попробуй снова.'}),
                'headers': {'Content-Type': 'application/json'}
            }

        reply = response.json()['choices'][0]['message']['content']
        return {
            'statusCode': 200,
            'body': json.dumps({'reply': reply}),
            'headers': {
                'Content-Type': 'application/json'
            }
        }

    except Exception as e:
        print(f"Error: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'reply': 'Я всё ещё здесь... Попробуй снова.'}),
            'headers': {'Content-Type': 'application/json'}
        }
