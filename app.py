from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS # Ver o result no swagger e outros sistemas
from flask_login import UserMixin, login_user, logout_user, LoginManager, login_required, current_user
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URI')

login_manager = LoginManager()
db = SQLAlchemy(app)
login_manager.init_app(app)
login_manager.login_view = 'login' # Rota que iremos autenticar o usuário
CORS(app)


class User(db.Model, UserMixin): # UserMixin utilizado para realizar o Login
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), nullable=False, unique=True)
    password = db.Column(db.String(80), nullable=True)
    # lazy=True => Só vai recuperar a playlist quando vc tentar acessar essa info
    playlist = db.relationship('Playlist', backref='user', lazy=True) # Recuperação da playlist do usuário

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


@app.route('/api/musics/<int:music_id>', methods=["GET"])
def get_music_details(music_id):
    music = Music.query.get(music_id)
    if music:
        return jsonify({
            "id": music.id,
            "name": music.name,
            "artist": music.artist,
            "time": music.time,
            "description": music.description
        })
    return jsonify({"message": "Music not found"}), 404


@app.route('/api/musics/add', methods=["POST"])
def add_music():
    data = request.json
    if 'name' in data and 'artist' in data and 'time' in data:
        music = Music(name=data["name"], artist=data["artist"], time=data["time"], description=data.get("description", ""))
        db.session.add(music)
        db.session.commit()
        return jsonify({"message": "Music added successfully"})
    return jsonify({"message": "Invalid music data"})


@app.route('/api/musics/update/<int:music_id>', methods=["PUT"])
def update_music(music_id):
    music = Music.query.get(music_id)
    if not music:
        return jsonify({"message": "Music not found"}), 404
    
    data = request.json
    if 'name' in data:
        music.name = data['name']
    
    if 'artist' in data:
        music.artist = data['artist']

    if 'time' in data:
        music.time = data['time']

    if 'description' in data:
        music.description = data['description']
    
    db.session.commit()
    return jsonify({'message': 'Music updated successfully'})


@app.route('/api/musics/delete/<int:music_id>', methods=["DELETE"])
def delete_music(music_id):
    music = Music.query.get(music_id)
    if music:
        db.session.delete(music)
        db.session.commit()
        return jsonify({"message": "Music deleted successfully"})
    return jsonify({"message": "Music not found"}), 404


@app.route('/')
def hello_world():
    return 'Hello World'

if __name__ == "__main__":
    app.run(debug=True)