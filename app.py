import os
import math
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
from groq import Groq
import firebase_admin
from firebase_admin import credentials, db

# Config
load_dotenv()
app = Flask(__name__)

groq_client = None  # Initialized only if GROQ_API_KEY is present
if os.getenv('GROQ_API_KEY'):
    try:
        groq_client = Groq(api_key=os.getenv('GROQ_API_KEY'))
    except Exception as e:
        print(f"Error initializing Groq: {e}")

firebase_cred_path = os.getenv('FIREBASE_CREDENTIALS_PATH')
firebase_db_url = os.getenv('FIREBASE_DATABASE_URL')

if firebase_cred_path and firebase_db_url:
    try:
        cred = credentials.Certificate(firebase_cred_path)
        firebase_admin.initialize_app(cred, {'databaseURL': firebase_db_url})
        print("Firebase connected successfully!")
    except Exception as e:
        print(f"Error initializing Firebase: {e}")
else:
    print("WARNING: Firebase credentials not configured. Set FIREBASE_CREDENTIALS_PATH and FIREBASE_DATABASE_URL in .env")

@app.route('/')
def index():
    return render_template('index.html')

SEVERE_TERMS = [
    "unconscious",
    "not breathing",
    "no pulse",
    "heart",
    "attack",
    "bleeding",
    "khoon",
    "seizure"
]

SYMPTOM_TERMS = [
    "dard",
    "pain",
    "fever",
    "burn",
    "fracture",
    "snake",
    "bite",
    "vomit"
]

RISK_TERMS = [
    "gir gaye",
    "accident",
    "breathe",
    "help",
    "emergency",
    "urgent",
    "collapse",
    "choking"
]

CASUAL_TERMS = [
    "hi",
    "hello",
    "hey",
    "how are you",
    "good morning",
    "good evening",
    "thanks",
    "thank you",
    "ok",
    "okay",
    "test",
    "ping"
]



def parse_float(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None




def score_emergency(message):
    # Simple scoring to classify emergencies based on keywords.
    text = (message or "").lower()
    score = 0

    if any(term in text for term in SEVERE_TERMS):
        score += 3
    if any(term in text for term in SYMPTOM_TERMS):
        score += 2
    if any(term in text for term in RISK_TERMS):
        score += 1

    is_emergency = score >= 3
    return is_emergency, score


def is_casual_message(message):
    text = (message or "").lower().strip()
    if not text:
        return False

    return any(term in text for term in CASUAL_TERMS)

@app.route('/api/chat', methods=['POST'])
def chat():
    # Main chat endpoint: returns AI reply and emergency classification.
    data = request.json or {}
    user_message = data.get('message', '')
    user_lat = parse_float(data.get('lat'))
    user_lng = parse_float(data.get('lng'))
    emergency_detected, emergency_score = score_emergency(user_message)
    casual_detected = is_casual_message(user_message)

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
            "If the situation is critical, advise them to seek immediate medical help while providing interim steps. "
            "Reply in the same language as the user's message."
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

        response_payload = {
            'reply': ai_reply,
            'emergency': emergency_detected,
            'emergency_score': emergency_score,
            'casual': casual_detected
        }

        if emergency_detected:
            if user_lat is None or user_lng is None:
                response_payload['volunteer_error'] = 'Location missing. Unable to find a volunteer.'
            else:
                nearest_volunteer, volunteer_error, _ = find_nearest_volunteer(user_lat, user_lng)

                if nearest_volunteer:
                    response_payload['volunteer'] = nearest_volunteer
                else:
                    response_payload['volunteer_error'] = volunteer_error

        return jsonify(response_payload)

    except Exception as e:
        print(f"Error calling Groq API: {e}")
        return jsonify({'error': 'Failed to process request. Please try again or seek immediate help.'}), 500

@app.route('/api/seed-volunteers', methods=['GET', 'POST'])
def seed_volunteers():
    # Adds a fixed set of demo volunteers to Firebase.
    volunteers = [
        {
            "name": "Rahul Sharma",
            "phone": "9876543210",
            "lat": 18.5204,
            "lng": 73.8567,
            "skill": "CPR Trained",
            "status": "available"
        },
        {
            "name": "Priya Deshmukh",
            "phone": "9823456789",
            "lat": 18.5074,
            "lng": 73.8077,
            "skill": "First Aid Certified",
            "status": "available"
        },
        {
            "name": "Amit Patil",
            "phone": "9765432109",
            "lat": 18.4529,
            "lng": 73.8186,
            "skill": "Snake Bite Treatment",
            "status": "available"
        },
        {
            "name": "Sneha Kulkarni",
            "phone": "9654321098",
            "lat": 18.5590,
            "lng": 73.8080,
            "skill": "Wound Care Specialist",
            "status": "available"
        },
        {
            "name": "Vikram Jadhav",
            "phone": "9543210987",
            "lat": 18.4872,
            "lng": 73.8072,
            "skill": "Emergency Transport",
            "status": "available"
        },
        {
            "name": "Amit Deshmukh",
            "phone": "9823456701",
            "lat": 19.1350,
            "lng": 77.3180,
            "skill": "CPR Trained",
            "status": "available"
        },
        {
            "name": "Priya Kulkarni",
            "phone": "9823456702",
            "lat": 19.1400,
            "lng": 77.3250,
            "skill": "First Aid Expert",
            "status": "available"
        },
        {
            "name": "Rahul Patil",
            "phone": "9823456703",
            "lat": 19.1320,
            "lng": 77.3150,
            "skill": "Snake Bite Treatment",
            "status": "available"
        },
        {
            "name": "Shashank Zarikar",
            "phone": "your_phone_number",
            "lat": 19.18450476340424,
            "lng": 77.30401996683295,
            "skill": "First Responder",
            "status": "available"
        }
    ]

    try:
        ref = db.reference('volunteers')

        existing = ref.get() or {}
        existing_phones = {
            vol.get('phone')
            for vol in existing.values()
            if isinstance(vol, dict) and vol.get('phone')
        }

        added = 0
        skipped = 0

        for volunteer in volunteers:
            if volunteer.get('phone') in existing_phones:
                skipped += 1
                continue

            ref.push(volunteer)
            existing_phones.add(volunteer.get('phone'))
            added += 1

        return jsonify({
            'message': f'Seeded volunteers. Added: {added}, skipped: {skipped}.'
        })

    except Exception as e:
        print(f"Error seeding volunteers: {e}")
        return jsonify({'error': f'Failed to seed volunteers: {str(e)}'}), 500

def haversine(lat1, lng1, lat2, lng2):
    """Return distance in km using the Haversine formula."""
    R = 6371
    d_lat = math.radians(lat2 - lat1)
    d_lng = math.radians(lng2 - lng1)
    a = (
        math.sin(d_lat / 2) ** 2 +
        math.cos(math.radians(lat1)) *
        math.cos(math.radians(lat2)) *
        math.sin(d_lng / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

def find_nearest_volunteer(user_lat, user_lng):
    # Finds the nearest available volunteer from Firebase.
    if user_lat is None or user_lng is None:
        return None, 'Please provide both lat and lng', 400

    try:
        ref = db.reference('volunteers')
        all_volunteers = ref.get()
        if not all_volunteers:
            return None, 'No volunteers found in database', 404
        nearest = None
        min_distance = float('inf')
        for vol_id, vol_data in all_volunteers.items():
            if vol_data.get('status') != 'available':
                continue
            distance = haversine(
                user_lat, user_lng,
                vol_data['lat'], vol_data['lng']
            )
            if distance < min_distance:
                min_distance = distance
                distance_display = f"{distance:.2f}"
                if distance < 0.1:
                    distance_display = "0.0"
                nearest = {
                    'id': vol_id,
                    'name': vol_data['name'],
                    'phone': vol_data['phone'],
                    'skill': vol_data['skill'],
                    'distance_km': distance_display,
                    'lat': vol_data['lat'],
                    'lng': vol_data['lng']
                }
        if nearest:
            return nearest, None, 200
        else:
            return None, 'No available volunteers found', 404

    except Exception as e:
        print(f"Error finding volunteer: {e}")
        return None, f'Failed to find volunteer: {str(e)}', 500

@app.route('/api/find-volunteer', methods=['GET', 'POST'])
def find_volunteer():
    # Returns the nearest available volunteer for the given coordinates.
    if request.method == 'GET':
        user_lat = request.args.get('lat', type=float)
        user_lng = request.args.get('lng', type=float)
    else:
        data = request.json or {}
        user_lat = parse_float(data.get('lat'))
        user_lng = parse_float(data.get('lng'))

    nearest, error_message, status_code = find_nearest_volunteer(user_lat, user_lng)

    if nearest:
        return jsonify({'volunteer': nearest})
    else:
        return jsonify({'error': error_message}), status_code


@app.route('/api/cleanup-volunteers', methods=['POST'])
def cleanup_volunteers():
    # Removes duplicate volunteers by phone number.
    try:
        ref = db.reference('volunteers')
        all_volunteers = ref.get() or {}

        seen_phones = set()
        removed = 0

        for vol_id, vol_data in all_volunteers.items():
            phone = None
            if isinstance(vol_data, dict):
                phone = vol_data.get('phone')

            if not phone or phone in seen_phones:
                ref.child(vol_id).delete()
                removed += 1
                continue

            seen_phones.add(phone)

        return jsonify({'message': f'Removed {removed} duplicate volunteers.'})
    except Exception as e:
        print(f"Error cleaning volunteers: {e}")
        return jsonify({'error': f'Failed to clean volunteers: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(debug=True)
