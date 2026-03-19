import os
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
from groq import Groq

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

# Initialize Groq client
groq_client = None
if os.getenv('GROQ_API_KEY'):
    try:
        groq_client = Groq(api_key=os.getenv('GROQ_API_KEY'))
    except Exception as e:
        print(f"Error initializing Groq: {e}")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.json
    user_message = data.get('message', '')

    if not user_message:
        return jsonify({'error': 'No message provided'}), 400

    if not groq_client:
        return jsonify({
            'reply': 'AI is currently offline. Please call local emergency services immediately if this is a life-threatening situation.'
        })

    try:
        system_prompt = (
            "You are GoldenMinute AI, an emergency response assistant for rural India. "
            "Your goal is to provide immediate, actionable, and culturally relevant first-aid "
            "and emergency advice. Keep your responses concise, clear, and easy to understand. "
            "If the situation is critical, advise them to seek immediate medical help while providing interim steps."
        )

        chat_completion = groq_client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            model="llama-3.3-70b-versatile",
            temperature=0.3,
            max_tokens=500
        )

        ai_reply = chat_completion.choices[0].message.content

        return jsonify({'reply': ai_reply})

    except Exception as e:
        print(f"Error calling Groq API: {e}")
        return jsonify({'error': 'Failed to process request. Please try again or seek immediate help.'}), 500

if __name__ == '__main__':
    app.run(debug=True)
