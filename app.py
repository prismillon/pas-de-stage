import threading
import asyncio
import aiohttp

from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///mydatabase.db'
app.secret_key = 'KKejzgbjzoei'
db = SQLAlchemy(app)

api_url = "https://www.balldontlie.io/api/v1/"

player_list = {}
team_list = {}
game_list = {}


async def fetch_api():
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{api_url}players?per_page=100&page=0") as response:
            if response.status == 200:
                data = await response.json()

                for page in range(data['meta']['total_pages']):
                    async with session.get(f"{api_url}players?per_page=100&page={page}") as response:
                        if response.status == 200:
                            print(f"player request n°{page+1}/{data['meta']['total_pages']} success")
                            player_data = await response.json()
                            for player in player_data['data']:
                                player_list[player['id']] = player
                            await asyncio.sleep(1)
                        else:
                            print(f"player request n°{page+1} error {response.status} aborting")
                            exit()

        async with session.get(f"{api_url}teams?page=0") as response:
            if response.status == 200:
                data = await response.json()

                for page in range(data['meta']['total_pages']):
                    async with session.get(f"{api_url}teams?page={page}") as response:
                        if response.status == 200:
                            print(f"team request n°{page+1}/{data['meta']['total_pages']} success")
                            team_data = await response.json()
                            for team in team_data['data']:
                                team_list[team['id']] = team
                            await asyncio.sleep(1)
                        else:
                            print(f"team request n°{page+1} error {response.status} aborting")
                            exit()

        async with session.get(f"{api_url}games?per_page=100&page=0") as response:
            if response.status == 200:
                data = await response.json()

                for page in range(data['meta']['total_pages']):
                    async with session.get(f"{api_url}games?per_page=100&page={page}") as response:
                        if response.status == 200:
                            print(f"game request n°{page+1}/{data['meta']['total_pages']} success")
                            games_data = await response.json()
                            for game in games_data['data']:
                                game_list[game['id']] = game
                            await asyncio.sleep(1)
                        else:
                            print(f"game request n°{page+1} error {response.status} aborting")
                            exit()

# Define your User model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)

def run_api():
    asyncio.run(fetch_api())

# Create the database tables
with app.app_context():
    db.create_all()
    fetch_thread = threading.Thread(target=run_api)
    fetch_thread.start()

# Define routes
@app.route('/')
def home():
    if 'username' in session:
        #return player_list
        return render_template('index.html', players=player_list.values(), teams=team_list.values(), games=game_list.values())

    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'username' in session:
        return redirect(url_for('home'))
    error = None  # Initialize an error variable
    
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username, password=password).first()
        if user:
            session['username'] = username  # Store username in the session
            return redirect(url_for('home'))  # Redirect to the main page
        else:
            error = "Login failed. Please check your credentials."
    
    return render_template('login.html', error=error)  # Pass the error to the template


@app.route('/register', methods=['GET', 'POST'])
def register():
    if 'username' in session:
        return redirect(url_for('home'))

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        # Check if the username already exists in the database
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            error_message = "Username already exists. Please choose a different one."
            return render_template('register.html', error=error_message)
        
        user = User(username=username, password=password)
        db.session.add(user)
        db.session.commit()
        session['username'] = username  # Store username in the session
        return redirect(url_for('home'))  # Redirect to the main page
    
    return render_template('register.html')

@app.route('/logout', methods=['GET', 'POST'])
def logout():
    session.pop('username', None)  # Remove username from the session
    return render_template('logout_confirmation.html')


@app.route('/player/<id>')
async def player(id):
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{api_url}players/{id}") as response:
            if response.status == 200:
                player = await response.json()
    
    if player:
        return render_template('player.html', player=player)
    else:
        # Handle the case where the player with the given ID is not found
        return "Player not found", 404

@app.route('/team/<id>')
def team(id):
    team = team_list[int(id)]
    team_players = []

    if team:
        for data in player_list.values():
            if 'team' in data and data['team']['id'] == team['id']:
                team_players.append(data)
        return render_template('team.html', teams=team, team_players=team_players)
    else:
        return "Team not found", 404

@app.route('/game/<id>')
async def game(id):
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{api_url}games/{id}") as response:
            if response.status == 200:
                game = await response.json()
    
    if game:
        return render_template('game.html', match=game)
    else:
        return "Game not found", 404


if __name__ == '__main__':
    app.run()
