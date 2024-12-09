from flask import Flask, request, jsonify, send_from_directory
import sqlite3
import os
import uuid

class Game:
    def __init__(self, name, genre, release_date, image):
        self.id = uuid.uuid4().hex
        self.name = name
        self.genre = genre
        self.release_date = release_date
        self.image = image

app = Flask(__name__)

# Upload folder configuration
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Database initialization
def connect_db():
    with sqlite3.connect('game_store.db') as db:
        c = db.cursor()
        c.execute("""
            CREATE TABLE IF NOT EXISTS GAMES (
                id TEXT PRIMARY KEY,
                name TEXT,
                genre TEXT,
                release_date TEXT,
                image TEXT
            )
        """)
        db.commit()

@app.route('/homepage', methods=['GET'])
def get_homepage():
    with sqlite3.connect('game_store.db') as db:
        cursor = db.cursor()
        cursor.execute("SELECT * FROM GAMES ORDER BY genre, release_date DESC")
        data = cursor.fetchall()
        games_by_genre = {}
        unique_games = {}

        for row in data:
            game_id, name, genre, release_date, image = row
            if (name, genre, release_date) not in unique_games:
                unique_games[(name, genre, release_date)] = {
                    "id": game_id,
                    "name": name,
                    "genre": genre,
                    "release_date": release_date,
                    "image": image
                }
                if genre not in games_by_genre:
                    games_by_genre[genre] = []
                games_by_genre[genre].append(unique_games[(name, genre, release_date)])

        featured_games = sorted(unique_games.values(), key=lambda x: x["release_date"], reverse=True)[:3]

        response = {
            "featured_games": featured_games,
            "games_by_genre": games_by_genre
        }
        return jsonify(response)

@app.route('/addGame', methods=['POST'])
def add_game():
    name = request.form['name']
    genre = request.form['genre']
    release_date = request.form['release_date']
    image = request.files.get('image')
    image_filename = None
    if image:
        image_filename = os.path.join(app.config['UPLOAD_FOLDER'], image.filename)
        image.save(image_filename)

    with sqlite3.connect('game_store.db') as db:
        cursor = db.cursor()
        cursor.execute("SELECT * FROM GAMES WHERE name = ? AND genre = ? AND release_date = ?", (name, genre, release_date))
        existing_game = cursor.fetchone()
        if existing_game:
            return jsonify({"message": "Game already exists!"}), 400

        game = Game(name, genre, release_date, image_filename)
        cursor.execute(
            "INSERT INTO GAMES (id, name, genre, release_date, image) VALUES (?, ?, ?, ?, ?)",
            (game.id, game.name, game.genre, game.release_date, game.image)
        )
        db.commit()

    return jsonify({"message": "Game added successfully!", "game_id": game.id}), 201

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    connect_db()
    app.run(debug=True, port=1241)
