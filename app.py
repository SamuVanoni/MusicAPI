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

class Playlist(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False) # FK do userId
    music_id = db.Column(db.Integer, db.ForeignKey('music.id'), nullable=False)


# Autenticacao
@login_manager.user_loader # Recupera o usuário que vai acessar a rota
def load_user(user_id): # Quem chama ele é o login_required
    return User.query.get(int(user_id))


@app.route('/create_user', methods=["POST"])
def create_user():
    data = request.json
    if 'username' in data and 'password' in data:
        user = User(username=data["username"], password=data["password"])
        db.session.add(user)
        db.session.commit()
        return jsonify({"message": "User added successfully"})
    return jsonify({"message": "Invalid user data"})


@app.route('/delete_user/<int:user_id>', methods=["DELETE"])
def delete_user(user_id):
    user = User.query.get(user_id)
    if user:
        playlist_items = user.playlist
        for playlist_item in playlist_items: # Excluindo a playlist do usuário
            db.session.delete(playlist_item)
        db.session.delete(user) # Excluindo o usuário
        db.session.commit()
        return jsonify({"message": "User deleted successfully"})
    return jsonify({"message": "User not found"}), 404


@app.route('/login', methods=["POST"])
def login():
    data = request.json
    # filter_by -> fazer busca sem ser pela PK (id)
    user = User.query.filter_by(username=data.get("username")).first()
    # Retornaria uma lista, o .first() é utilizado p pegar somente o 1°

    if user and data.get("password") == user.password:
        login_user(user)
        return jsonify({"message": "Logged in successfully"})
    return jsonify({"message": "Unauthorized. Invalid credentials"}), 401


@app.route('/logout', methods=["POST"])
@login_required
def logout():
    logout_user()
    return jsonify({"message": "Logout successfully"})


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
@login_required
def add_music():
    data = request.json
    if 'name' in data and 'artist' in data and 'time' in data:
        music = Music(name=data["name"], artist=data["artist"], time=data["time"], description=data.get("description", ""))
        db.session.add(music)
        db.session.commit()
        return jsonify({"message": "Music added successfully"})
    return jsonify({"message": "Invalid music data"})


@app.route('/api/musics/update/<int:music_id>', methods=["PUT"])
@login_required
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
@login_required
def delete_music(music_id):
    music = Music.query.get(music_id)
    if music:
        db.session.delete(music)
        db.session.commit()
        return jsonify({"message": "Music deleted successfully"})
    return jsonify({"message": "Music not found"}), 404


# Playlist
@app.route('/api/playlist', methods=['GET'])
@login_required
def view_playlist():
    # Pegando o Usuario
    user = User.query.get(int(current_user.id))
    playlist_items = user.playlist # MT EASY DE RECUPERAR AS MÚSICAS!!!
    playlist_content = []
    for playlist_item in playlist_items:
        music = Music.query.get(playlist_item.music_id) # Para retornar o nome, tempo e artista das músicas
        playlist_content.append({
                                "id": playlist_item.id,
                                #"user_id": playlist_item.user_id,
                                #"music_id": playlist_item.product_id,
                                "music_name": music.name,
                                "music_artist": music.artist,
                                "music_time": music.time,
                            })
    return jsonify(playlist_content)


@app.route('/api/playlist/add/<int:music_id>', methods=['POST'])
@login_required
def add_to_playlist(music_id):
    # Pegando o Usuario
    user = User.query.get(int(current_user.id))
    # Pegando a Música
    music = Music.query.get(music_id)

    if user and music:
        playlist_item = Playlist(user_id=user.id, music_id=music.id) # Criando o CartItem (instanciando)
        db.session.add(playlist_item) # Add no carrinho do cliente
        db.session.commit() # Finalizando
        return jsonify({'message': 'Item added to the playlist successfully'})
    return jsonify({'message': 'Failed to add item to the playlist'}), 400


@app.route('/api/playlist/remove/<int:music_id>', methods=['DELETE'])
@login_required
def remove_from_playlist(music_id):
    # Buscamos o item da playlist que tem o current_user.id e a music que está pedindo para remover
    music_item = Playlist.query.filter_by(user_id=current_user.id, music_id=music_id).first()
    if music_item:
        db.session.delete(music_item)
        db.session.commit()
        return jsonify({'message': 'Music removed from the playlist successfully'})
    return jsonify({'message': 'Failed to remove music from the playlist'}), 400


@app.route('/')
def hello_world():
    return 'Hello World'

if __name__ == "__main__":
    app.run(debug=True)