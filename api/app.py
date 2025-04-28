import os
import base64
import json
import urllib.parse
import pika
from flask import Flask, request, redirect, session
from flask_cors import CORS
from db import SessionLocal, User, init_db
import spotify

# Flask app setup
app = Flask(__name__)
CORS(app, supports_credentials=True, origins=["http://localhost:3000","http://127.0.0.1:3000"])
app.secret_key = os.getenv("FLASK_SECRET_KEY", "supersecretkey")


# Load config from env
SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
SPOTIFY_REDIRECT_URI = os.getenv("SPOTIFY_REDIRECT_URI")

RABBITMQ_HOST = os.getenv("RABBITMQ_HOST")
RABBITMQ_QUEUE = os.getenv("RABBITMQ_QUEUE")

# Database
init_db()

def publish_to_rabbitmq(xml_content, user_id):
    retries = 5
    delay = 3  # seconds between retries

    for attempt in range(retries):
        try:
            connection = pika.BlockingConnection(
                pika.ConnectionParameters(
                    host=os.getenv("RABBITMQ_HOST", "rabbitmq"),
                    credentials=pika.PlainCredentials('guest', 'guest')
                )
            )
            break
        except pika.exceptions.AMQPConnectionError as e:
            print(f"🚨 RabbitMQ connection failed ({attempt+1}/{retries}), retrying in {delay}s: {e}", flush=True)
            time.sleep(delay)
    else:
        raise Exception("🚨 Could not connect to RabbitMQ after retries")

    channel = connection.channel()
    channel.queue_declare(queue=os.getenv("RABBITMQ_QUEUE", "rekordbox_jobs"), durable=True)

    xml_b64 = base64.b64encode(xml_content).decode('utf-8')

    message = {
        "user_id": user_id,
        "xml_content_b64": xml_b64
    }

    channel.basic_publish(
        exchange='',
        routing_key=os.getenv("RABBITMQ_QUEUE", "rekordbox_jobs"),
        body=json.dumps(message)
    )
    connection.close()

@app.route('/login')
def login():
    params = {
        "client_id": SPOTIFY_CLIENT_ID,
        "response_type": "code",
        "redirect_uri": SPOTIFY_REDIRECT_URI,
        "scope": "playlist-read-private playlist-modify-private playlist-modify-public",
    }
    auth_url = "https://accounts.spotify.com/authorize?" + urllib.parse.urlencode(params)
    return redirect(auth_url)

@app.route('/callback')
def callback():
    code = request.args.get('code')
    token_data = spotify.exchange_code_for_token(code)

    # Save user into DB
    sp = spotify.SpotifyAPI(token_data["access_token"])
    user_profile = sp.get_user_profile()

    db = SessionLocal()
    user = db.query(User).filter(User.id == user_profile["id"]).first()
    if not user:
        user = User(id=user_profile["id"], display_name=user_profile["display_name"], refresh_token=token_data["refresh_token"])
        db.add(user)
    else:
        user.refresh_token = token_data["refresh_token"]
    db.commit()
    db.close()

    session['user_id'] = user_profile["id"]

    
    return redirect("http://127.0.0.1:3000")


import sys
from flask import jsonify

@app.route('/upload', methods=['POST'])
def upload():
    try:
        print("✅ Entering upload route", flush=True)
        
        if 'user_id' not in session:
            print("🚨 No user_id in session", flush=True)
            return "Unauthorized", 401

        if 'file' not in request.files:
            print("🚨 No file uploaded", flush=True)
            return "No file uploaded.", 400

        file = request.files['file']
        xml_content = file.read()

        if not xml_content:
            print("🚨 Uploaded file is empty", flush=True)
            return "Empty file uploaded.", 400

        print("✅ Publishing to RabbitMQ...", flush=True)
        publish_to_rabbitmq(xml_content, session['user_id'])
        
        print("✅ Successfully queued XML", flush=True)
        return "✅ File uploaded and queued!", 200

    except Exception as e:
        print(f"🔥 Exception inside /upload: {repr(e)}", flush=True)
        sys.stdout.flush()
        sys.stderr.flush()
        return jsonify({"error": str(e)}), 500

@app.errorhandler(Exception)
def handle_exception(e):
    return {"error": str(e)}, 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3001, debug=True)

