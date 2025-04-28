import os
import pika
from db import SessionLocal, Playlist, Track, User
import spotify
from pyrekordbox import RekordboxXml
import json


RABBITMQ_HOST = os.getenv("RABBITMQ_HOST")
RABBITMQ_QUEUE = os.getenv("RABBITMQ_QUEUE")

def process_rekordbox(xml_content, user_id):
    db = SessionLocal()

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        print(f"⚠️ User {user_id} not found!")
        return

    sp = spotify.SpotifyAPI(user.refresh_token)  # You would refresh token here if expired in real-world
    xml = RekordboxXml(xml_content)

    for track in xml.get_tracks():
        el = track._element
        name = el.get("Name") or ""
        artist = el.get("Artist") or ""
        colour = el.get("Colour") or ""

        # Simulated playlist creation for this MVP (later: group by playlists properly)
        playlist = db.query(Playlist).filter(Playlist.user_id == user_id, Playlist.name == "Default Playlist").first()
        if not playlist:
            playlist = Playlist(id=f"pl_{user_id}", name="Default Playlist", user_id=user_id)
            db.add(playlist)
            db.commit()

        t = Track(id=f"{name}_{artist}", name=name, artist=artist, colour=colour, playlist_id=playlist.id, user_id=user_id)
        db.merge(t)

    db.commit()
    db.close()
    print(f"✅ Processed Rekordbox upload for user {user_id}")


def main():
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(
            host=os.getenv("RABBITMQ_HOST", "rabbitmq"),
            credentials=pika.PlainCredentials('guest', 'guest')
        )
    )
    channel = connection.channel()
    channel.queue_declare(queue=os.getenv("RABBITMQ_QUEUE", "rekordbox_jobs"), durable=True)

    def callback(ch, method, properties, body):
        try:
            message = json.loads(body)
            user_id = message["user_id"]
            xml_b64 = message["xml_content_b64"]

            xml_content = base64.b64decode(xml_b64)

            process_rekordbox(xml_content, user_id)
            ch.basic_ack(delivery_tag=method.delivery_tag)
        except Exception as e:
            print(f"🔥 Worker crash processing message: {e}", flush=True)
            ch.basic_nack(delivery_tag=method.delivery_tag)

    channel.basic_consume(queue=os.getenv("RABBITMQ_QUEUE", "rekordbox_jobs"), on_message_callback=callback)
    print("🚀 Worker started, waiting for Rekordbox uploads...")
    channel.start_consuming()

if __name__ == "__main__":
    main()

