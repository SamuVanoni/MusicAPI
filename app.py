from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS # Ver o result no swagger e outros sistemas
from flask_login import UserMixin, login_user, logout_user, LoginManager, login_required, current_user
from dotenv import load_dotenv
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URI')

db = SQLAlchemy(app)


class Music(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    artist = db.Column(db.String(120), nullable=False)
    time = db.Column(db.Float, nullable=False)
    description = db.Column(db.Text, nullable=True)


# Rotas Musics
@app.route('/api/musics', methods=["GET"])
def get_musics():
    musics = Music.query.all()
    music_list = []
    for music in musics:
        music_data = {
            "id": music.id,
            "name": music.name,
            "artist": music.artist,
            "time": music.time,
        }
        music_list.append(music_data)
    return jsonify(music_list)


@app.route('/api/musics/add', methods=["POST"])
@login_required
def add_music():
    data = request.json
    if 'name' in data and 'artist' in data and 'time' in data:
        music = Music(name=data["name"], artist=data["artist"], time=data["time"], description=data.get("description", ""))
        db.session.add(music)
        db.session.commit()
        return jsonify({"message": "Music added successfully"})
    return jsonify({"message": "Invalid music data"})


@app.route('/')
def hello_world():
    return 'Hello World'

if __name__ == "__main__":
    app.run(debug=True)