import json
import os
import requests
from http import HTTPStatus

def handler(request):
    if request.method != 'POST':
        return {
            'statusCode': HTTPStatus.METHOD_NOT_ALLOWED,
            'body': json.dumps({'error': 'Only POST requests are allowed'})
        }

    try:
        data = request.get_json()
        message = data.get('message')
        if not message:
            return {
                'statusCode': HTTPStatus.BAD_REQUEST,
                'body': json.dumps({'error': 'Message is required'})
            }

        # Вызов OpenRouter API
        response = requests.post(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {os.getenv('OPENROUTER_API_KEY')}",
                "Content-Type": "application/json",
                "HTTP-Referer": os.getenv('SITE_URL', 'https://your-site.vercel.app'),
                "X-Title": os.getenv('SITE_NAME', 'Mirror Project')
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
            return {
                'statusCode': HTTPStatus.INTERNAL_SERVER_ERROR,
                'body': json.dumps({'reply': 'Я всё ещё здесь... Попробуй снова.'})
            }

        reply = response.json()['choices'][0]['message']['content']
        return {
            'statusCode': HTTPStatus.OK,
            'body': json.dumps({'reply': reply}),
            'headers': {
                'Content-Type': 'application/json',
                'Cache-Control': 'no-store'
            }
        }

    except Exception as e:
        print(f"Error: {str(e)}")
        return {
            'statusCode': HTTPStatus.INTERNAL_SERVER_ERROR,
            'body': json.dumps({'reply': 'Я всё ещё здесь... Попробуй снова.'})
        }
