from flask import Blueprint, jsonify
import requests
import random

reddit_story = Blueprint('reddit_story', __name__)

SUBREDDITS = ["nosleep", "creepy"]

@reddit_story.route('/api/creepy-story', methods=['GET'])
def get_creepy_story():
    # Можно чередовать сабреддиты
    subreddit = random.choice(SUBREDDITS)
    url = f"https://www.reddit.com/r/{subreddit}/top.json?limit=50&t=month"
    headers = {"User-Agent": "h0rr0rbot/1.0"}
    try:
        response = requests.get(url, headers=headers, timeout=5)
        posts = response.json()['data']['children']
        stories = [p['data'] for p in posts if p['data']['selftext'] and not p['data']['stickied'] and len(p['data']['selftext']) > 250]
        if not stories:
            return jsonify({'error': 'Нет подходящих историй'}), 500
        story = random.choice(stories)
        return jsonify({
            'title': story['title'],
            'text': story['selftext']
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500
