# ============================================================
# IMPORTS — Loading all the libraries we need
# ============================================================

import os                          # 'os' lets us read environment variables (like API keys) from the system
import math                        # 'math' gives us mathematical functions (sin, cos, sqrt, etc.) for the Haversine formula
from flask import Flask, render_template, request, jsonify
                                   # Flask       — the web framework that runs our server
                                   # render_template — serves HTML files from the templates/ folder
                                   # request     — lets us read data sent by the frontend (like JSON body)
                                   # jsonify     — converts Python dictionaries into JSON responses
from dotenv import load_dotenv     # 'load_dotenv' reads the .env file and loads its values into os.environ
from groq import Groq              # 'Groq' is the client library to talk to Groq's AI API
import firebase_admin              # 'firebase_admin' is Google's official SDK to interact with Firebase services
from firebase_admin import credentials, db
                                   # credentials — used to authenticate our app with Firebase using a service account key
                                   # db          — gives us methods to read/write data in Firebase Realtime Database

# ============================================================
# CONFIGURATION — Load environment variables
# ============================================================

load_dotenv()
# ^ Reads the .env file in the project root and loads every KEY=VALUE pair
#   into Python's os.environ, so we can access them with os.getenv('KEY')

# ============================================================
# FLASK APP — Create the web application
# ============================================================

app = Flask(__name__)
# ^ Creates a new Flask web application.
#   __name__ tells Flask where to find templates/ and static/ folders.

# ============================================================
# GROQ AI — Initialize the AI client
# ============================================================

groq_client = None                 # Start with no client; we'll create one only if the API key exists
if os.getenv('GROQ_API_KEY'):      # Check if 'GROQ_API_KEY' is set in the .env file
    try:
        groq_client = Groq(api_key=os.getenv('GROQ_API_KEY'))
        # ^ Creates a Groq client using the API key.
        #   This client will be used to send emergency messages to the AI model.
    except Exception as e:
        print(f"Error initializing Groq: {e}")
        # ^ If something goes wrong (invalid key format, etc.), print the error
        #   but don't crash the whole app — other features can still work.

# ============================================================
# FIREBASE — Initialize Firebase Admin SDK
# ============================================================

firebase_cred_path = os.getenv('FIREBASE_CREDENTIALS_PATH')
# ^ Reads the file path to your Firebase service account JSON key from .env
#   Example value: "firebase-key.json"

firebase_db_url = os.getenv('FIREBASE_DATABASE_URL')
# ^ Reads your Firebase Realtime Database URL from .env
#   Example value: "https://goldenminute-7e47e-default-rtdb.asia-southeast1.firebaseio.com"

if firebase_cred_path and firebase_db_url:
    # Only try to connect to Firebase if BOTH values are provided in .env
    try:
        cred = credentials.Certificate(firebase_cred_path)
        # ^ Loads the service account JSON file. This file contains your project's
        #   private key, which proves to Firebase that your app is authorized.

        firebase_admin.initialize_app(cred, {
            'databaseURL': firebase_db_url
        })
        # ^ Initializes the Firebase Admin SDK with:
        #   - Your credentials (authentication)
        #   - Your database URL (which database to connect to)
        #   This must be called exactly ONCE when the app starts.

        print("Firebase connected successfully!")
    except Exception as e:
        print(f"Error initializing Firebase: {e}")
else:
    print("WARNING: Firebase credentials not configured. Set FIREBASE_CREDENTIALS_PATH and FIREBASE_DATABASE_URL in .env")

# ============================================================
# ROUTE: Home Page — Serves the chat interface
# ============================================================

@app.route('/')
def index():
    # When a user visits http://127.0.0.1:5000/, Flask will:
    # 1. Look inside the templates/ folder for 'index.html'
    # 2. Render (process) that HTML file
    # 3. Send it back to the user's browser
    return render_template('index.html')

# ============================================================
# ROUTE: AI Chat — Handles emergency messages
# ============================================================

@app.route('/api/chat', methods=['POST'])
def chat():
    # This route only accepts POST requests (data sent from the frontend).
    # The frontend sends a JSON body like: {"message": "someone is choking"}

    data = request.json                        # Parse the JSON body from the request
    user_message = data.get('message', '')      # Extract the 'message' field; default to empty string if missing

    if not user_message:
        return jsonify({'error': 'No message provided'}), 400
        # ^ 400 = Bad Request. The frontend didn't send a message.

    if not groq_client:
        return jsonify({
            'reply': 'AI is currently offline. Please call local emergency services immediately if this is a life-threatening situation.'
        })
        # ^ If the Groq client failed to initialize (bad API key, etc.),
        #   return a helpful fallback message instead of crashing.

    try:
        system_prompt = (
            "You are GoldenMinute AI, an emergency response assistant for rural India. "
            "Your goal is to provide immediate, actionable, and culturally relevant first-aid "
            "and emergency advice. Keep your responses concise, clear, and easy to understand. "
            "If the situation is critical, advise them to seek immediate medical help while providing interim steps."
        )
        # ^ The system prompt tells the AI model WHO it is and HOW to behave.
        #   This is sent with every request so the AI stays in character.

        chat_completion = groq_client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                # ^ System message: sets the behavior/personality of the AI
                {"role": "user", "content": user_message}
                # ^ User message: the actual emergency description from the frontend
            ],
            model="llama-3.3-70b-versatile",   # The specific AI model to use on Groq
            temperature=0.3,                    # Low temperature = more focused, less creative responses
            max_tokens=500                      # Limit the response length to ~500 tokens
        )

        ai_reply = chat_completion.choices[0].message.content
        # ^ The API returns a list of choices. We take the first choice's message content.

        return jsonify({'reply': ai_reply})
        # ^ Send the AI's response back to the frontend as JSON: {"reply": "..."}

    except Exception as e:
        print(f"Error calling Groq API: {e}")
        return jsonify({'error': 'Failed to process request. Please try again or seek immediate help.'}), 500
        # ^ 500 = Internal Server Error. Something went wrong on the server side.

# ============================================================
# ROUTE: Seed Volunteers — Adds 5 test volunteers to Firebase
# ============================================================

@app.route('/api/seed-volunteers', methods=['GET', 'POST'])
def seed_volunteers():
    # This route creates 5 fake volunteer records in Firebase Realtime Database.
    # It's meant for TESTING purposes — so you can verify the database works.

    # A list of 5 volunteer dictionaries, each with different Pune locations.
    volunteers = [
        {
            "name": "Rahul Sharma",          # Volunteer's full name
            "phone": "9876543210",            # 10-digit Indian mobile number
            "lat": 18.5204,                   # Latitude of their location (Pune city center)
            "lng": 73.8567,                   # Longitude of their location
            "skill": "CPR Trained",           # What emergency skill they have
            "status": "available"             # Whether they're available to help right now
        },
        {
            "name": "Priya Deshmukh",
            "phone": "9823456789",
            "lat": 18.5074,                   # Shivajinagar area, Pune
            "lng": 73.8077,
            "skill": "First Aid Certified",
            "status": "available"
        },
        {
            "name": "Amit Patil",
            "phone": "9765432109",
            "lat": 18.4529,                   # Sinhagad Road area, Pune
            "lng": 73.8186,
            "skill": "Snake Bite Treatment",
            "status": "available"
        },
        {
            "name": "Sneha Kulkarni",
            "phone": "9654321098",
            "lat": 18.5590,                   # Aundh area, Pune
            "lng": 73.8080,
            "skill": "Wound Care Specialist",
            "status": "available"
        },
        {
            "name": "Vikram Jadhav",
            "phone": "9543210987",
            "lat": 18.4872,                   # Kothrud area, Pune
            "lng": 73.8072,
            "skill": "Emergency Transport",
            "status": "available"
        }
    ]

    try:
        ref = db.reference('volunteers')
        # ^ Gets a reference to the 'volunteers' node in Firebase Realtime Database.
        #   Think of it like pointing to a specific "folder" in your database.
        #   If it doesn't exist yet, Firebase will create it automatically.

        for volunteer in volunteers:
            ref.push(volunteer)
            # ^ 'push()' adds a new child under 'volunteers' with a unique auto-generated key.
            #   Each volunteer gets its own unique ID (like "-NxYz123abc").
            #   This prevents overwriting — every push creates a NEW entry.

        return jsonify({
            'message': f'Successfully added {len(volunteers)} volunteers to Firebase!'
        })
        # ^ Send a success message back as JSON.

    except Exception as e:
        print(f"Error seeding volunteers: {e}")
        return jsonify({'error': f'Failed to seed volunteers: {str(e)}'}), 500

# ============================================================
# HAVERSINE FORMULA — Calculate distance between two GPS points
# ============================================================

def haversine(lat1, lng1, lat2, lng2):
    """
    Calculates the straight-line distance (in km) between two points
    on the Earth's surface using their latitude and longitude.

    The Haversine formula accounts for the Earth being a sphere,
    not a flat surface, giving accurate distances.

    Parameters:
        lat1, lng1 — Latitude & Longitude of point 1 (the user)
        lat2, lng2 — Latitude & Longitude of point 2 (the volunteer)

    Returns:
        Distance in kilometers (float)
    """

    R = 6371
    # ^ Radius of the Earth in kilometers.
    #   This constant is used to convert the angular distance into km.

    d_lat = math.radians(lat2 - lat1)
    # ^ Difference in latitude, converted from degrees to radians.
    #   math.radians() is needed because math.sin() and math.cos() expect radians.

    d_lng = math.radians(lng2 - lng1)
    # ^ Difference in longitude, converted from degrees to radians.

    a = (
        math.sin(d_lat / 2) ** 2 +
        math.cos(math.radians(lat1)) *
        math.cos(math.radians(lat2)) *
        math.sin(d_lng / 2) ** 2
    )
    # ^ 'a' is the square of half the chord length between the two points.
    #   This is the core of the Haversine formula:
    #   a = sin²(Δlat/2) + cos(lat1) × cos(lat2) × sin²(Δlng/2)

    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    # ^ 'c' is the angular distance in radians between the two points.
    #   atan2 gives us a more numerically stable result than asin.

    return R * c
    # ^ Multiply the angular distance by Earth's radius to get the
    #   actual distance in kilometers.

# ============================================================
# ROUTE: Find Nearest Volunteer — Uses Haversine to find closest
# ============================================================

@app.route('/api/find-volunteer', methods=['GET', 'POST'])
def find_volunteer():
    # This route accepts the user's GPS coordinates and returns
    # the nearest AVAILABLE volunteer from Firebase.

    if request.method == 'GET':
        user_lat = request.args.get('lat', type=float)
        user_lng = request.args.get('lng', type=float)
    else:
        data = request.json or {}              # Parse the JSON body from the request
        user_lat = data.get('lat')             # User's latitude  (e.g., 18.52)
        user_lng = data.get('lng')             # User's longitude (e.g., 73.85)

    if user_lat is None or user_lng is None:
        return jsonify({'error': 'Please provide both lat and lng'}), 400
        # ^ If the frontend forgot to send coordinates, return a 400 error.

    try:
        ref = db.reference('volunteers')
        # ^ Get a reference to the 'volunteers' node in Firebase.

        all_volunteers = ref.get()
        # ^ '.get()' downloads ALL the data under 'volunteers' as a Python dictionary.
        #   The structure looks like: { "-NxYz123abc": { "name": "Rahul", ... }, ... }

        if not all_volunteers:
            return jsonify({'error': 'No volunteers found in database'}), 404
            # ^ 404 = Not Found. The database is empty — no volunteers have been seeded yet.

        nearest = None                     # Will hold the closest volunteer's data
        min_distance = float('inf')        # Start with infinity so any real distance is smaller
        # ^ float('inf') is a special Python value meaning "infinity".
        #   We compare each volunteer's distance against this, and keep the smallest.

        for vol_id, vol_data in all_volunteers.items():
            # ^ .items() loops through each volunteer entry.
            #   vol_id   = the unique Firebase key (e.g., "-NxYz123abc")
            #   vol_data = the volunteer's data dictionary (name, phone, lat, lng, etc.)

            if vol_data.get('status') != 'available':
                continue
                # ^ Skip this volunteer if they're NOT available.
                #   'continue' immediately jumps to the next iteration of the loop.

            distance = haversine(
                user_lat, user_lng,                # Point 1: the user's location
                vol_data['lat'], vol_data['lng']   # Point 2: this volunteer's location
            )
            # ^ Calculate the distance between the user and this volunteer using Haversine.

            if distance < min_distance:
                min_distance = distance
                # ^ If this volunteer is closer than any we've seen before,
                #   update min_distance to this new shorter distance.

                nearest = {
                    'id': vol_id,                           # The Firebase unique key
                    'name': vol_data['name'],               # Volunteer's name
                    'phone': vol_data['phone'],             # Volunteer's phone number
                    'skill': vol_data['skill'],             # Their emergency skill
                    'distance_km': round(distance, 2),      # Distance rounded to 2 decimal places
                    'lat': vol_data['lat'],                 # Volunteer's latitude
                    'lng': vol_data['lng']                   # Volunteer's longitude
                }
                # ^ Build a clean response dictionary with only the info we need.

        if nearest:
            return jsonify({'volunteer': nearest})
            # ^ Return the closest volunteer as JSON.
        else:
            return jsonify({'error': 'No available volunteers found'}), 404

    except Exception as e:
        print(f"Error finding volunteer: {e}")
        return jsonify({'error': f'Failed to find volunteer: {str(e)}'}), 500

# ============================================================
# START THE SERVER
# ============================================================

if __name__ == '__main__':
    app.run(debug=True)
    # ^ Starts the Flask development server on http://127.0.0.1:5000
    #   debug=True means:
    #   1. The server auto-restarts when you save code changes
    #   2. Detailed error pages are shown in the browser if something breaks
