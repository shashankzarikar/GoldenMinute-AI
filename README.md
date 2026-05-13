# GoldenMinute-AI
AI-powered emergency response system for rural India. It provides first-aid guidance via AI, finds the nearest volunteer, and sends emergency alerts with map links.

## Features
- AI first-aid guidance (auto-replies in the user's language)
- Emergency vs non-emergency classification
- Nearest volunteer discovery with map display
- Volunteer registration (separate page)
- Email alerts to volunteers with Google Maps links
- Optional victim phone/address in alerts

## Project Structure
- `app.py` — Flask backend, Groq AI, Firebase, and email alerts
- `templates/index.html` — Emergency chat UI
- `templates/volunteer.html` — Volunteer registration page
- `static/main.js` — Chat logic + map display
- `static/volunteer.js` — Volunteer registration logic
- `static/style.css` — Styling

## Setup
1) Create and activate a virtual environment.
2) Install dependencies:

```bash
pip install -r requirements.txt
```

3) Create a `.env` file in the project root with:

```env
GROQ_API_KEY=your_groq_api_key
FIREBASE_CREDENTIALS_PATH=firebase-key.json
FIREBASE_DATABASE_URL=your_firebase_db_url

SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_gmail_address
SMTP_PASSWORD=your_gmail_app_password
SMTP_SENDER=your_gmail_address
```

4) Run the app:

```bash
python app.py
```

Open `http://127.0.0.1:5000` in your browser.

## Usage
### Emergency Chat
1) Enter symptoms in the chat.
2) Allow location access when prompted.
3) If emergency: AI reply + volunteer alert + map.
4) If non-emergency: AI reply + nearest volunteer contact (no alert).

### Volunteer Registration
Open `http://127.0.0.1:5000/volunteer` and register a volunteer.
Use **Use my current location** to auto-fill latitude/longitude.

## Notes
- Gmail SMTP requires an App Password (enable 2-step verification).
- Volunteer alerts include Google Maps links for quick navigation.
