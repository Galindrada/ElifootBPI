from flask import Flask, render_template, redirect, url_for, flash, request
from flask_socketio import SocketIO, emit
from sqlalchemy import desc
from models import db, User, Team, Player, Match, GameState
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
import os
import random

# --- App Configuration ---
app = Flask(__name__)
app.config['SECRET_KEY'] = 'a_very_secret_key_change_me'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///elifoot_main.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# --- Extensions Initialization ---
db.init_app(app)
bcrypt = Bcrypt(app)
socketio = SocketIO(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# --- Database Setup ---
def setup_database():
    if Team.query.first(): return
    teams_data = [
        {'name': 'SL Benfica', 'hometown': 'Seixal', 'foundation_year': 1904, 'stadium_capacity': 2721},
        {'name': 'Sporting CP', 'hometown': 'Alcochete', 'foundation_year': 1906, 'stadium_capacity': 1128},
        {'name': 'SC Braga', 'hometown': 'Braga', 'foundation_year': 1921, 'stadium_capacity': 28000},
        {'name': 'Racing Power', 'hometown': 'Seixal', 'foundation_year': 2020, 'stadium_capacity': 3000},
        {'name': 'Valadares Gaia FC', 'hometown': 'Vila Nova de Gaia', 'foundation_year': 2011, 'stadium_capacity': 750},
        {'name': 'SCU Torreense', 'hometown': 'Torres Vedras', 'foundation_year': 1917, 'stadium_capacity': 2000},
        {'name': 'CS Marítimo', 'hometown': 'Funchal', 'foundation_year': 1910, 'stadium_capacity': 2000},
        {'name': 'SF Damaiense', 'hometown': 'Amadora', 'foundation_year': 1938, 'stadium_capacity': 2000},
        {'name': 'FC Famalicão', 'hometown': 'Vila Nova de Famalicão', 'foundation_year': 1931, 'stadium_capacity': 500},
        {'name': 'Clube de Albergaria', 'hometown': 'Albergaria-a-Velha', 'foundation_year': 1890, 'stadium_capacity': 1500},
        {'name': 'Länk FC Vilaverdense', 'hometown': 'Vila Verde', 'foundation_year': 1953, 'stadium_capacity': 3000},
        {'name': 'Atlético Ouriense', 'hometown': 'Ourém', 'foundation_year': 1949, 'stadium_capacity': 260}
    ]
    for data in teams_data: db.session.add(Team(**data))
    db.session.commit()
    
    player_names = ['Ana', 'Sofia', 'Maria', 'Leonor', 'Beatriz', 'Mariana', 'Carolina', 'Inês', 'Lara', 'Matilde']
    player_surnames = ['Silva', 'Santos', 'Ferreira', 'Pereira', 'Oliveira', 'Costa', 'Rodrigues', 'Martins']
    for team in Team.query.all():
        for i in range(22):
            pos = 'GK' if i < 2 else 'DF' if i < 8 else 'MF' if i < 15 else 'FW'
            if pos == 'GK':
                stats = {'attack': random.randint(10,30), 'defense': random.randint(70,90), 'power': random.randint(60,80), 'shot': random.randint(10,30), 'set_pieces': random.randint(15,40)}
            elif pos == 'DF':
                stats = {'attack': random.randint(20,50), 'defense': random.randint(70,90), 'power': random.randint(65,85), 'shot': random.randint(15,45), 'set_pieces': random.randint(20,50)}
            elif pos == 'MF':
                stats = {'attack': random.randint(50,75), 'defense': random.randint(50,75), 'power': random.randint(50,75), 'shot': random.randint(45,70), 'set_pieces': random.randint(50,80)}
            else: # FW
                stats = {'attack': random.randint(70,90), 'defense': random.randint(20,45), 'power': random.randint(55,80), 'shot': random.randint(70,90), 'set_pieces': random.randint(40,65)}
            player = Player(name=f"{random.choice(player_names)} {random.choice(player_surnames)}", age=random.randint(18, 34), position=pos, skill=round(sum(stats.values())/len(stats)), team_id=team.id, **stats)
            db.session.add(player)
    db.session.commit()
    
    all_teams = Team.query.all()
    if len(all_teams) % 2 != 0: all_teams.append(None)
    n = len(all_teams)
    schedule = []
    for i in range(n - 1):
        round_fixtures = [];
        for j in range(n // 2):
            home, away = all_teams[j], all_teams[n - 1 - j]
            if home and away: round_fixtures.append((home, away))
        schedule.append(round_fixtures)
        all_teams.insert(1, all_teams.pop())
    for round_num, round_fixtures in enumerate(schedule, 1):
        for home_team, away_team in round_fixtures: db.session.add(Match(round=round_num, home_team_id=home_team.id, away_team_id=away_team.id))
    total_rounds = n - 1
    for round_num, round_fixtures in enumerate(schedule, 1):
        for home_team, away_team in round_fixtures: db.session.add(Match(round=round_num + total_rounds, home_team_id=away_team.id, away_team_id=home_team.id))
    db.session.add(GameState(key='current_round', value='1'))
    db.session.commit()

# --- Auth Routes ---
@app.route('/')
def landing_page():
    if current_user.is_authenticated: return redirect(url_for('dashboard'))
    return render_template('landing.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated: return redirect(url_for('dashboard'))
    if request.method == 'POST':
        if User.query.filter_by(username=request.form.get('username')).first():
            flash('Username already exists.', 'danger'); return redirect(url_for('register'))
        team_to_manage = Team.query.get(request.form.get('team_id'))
        if not team_to_manage or team_to_manage.manager:
            flash('Team is already taken or does not exist.', 'danger'); return redirect(url_for('register'))
        hashed_password = bcrypt.generate_password_hash(request.form.get('password')).decode('utf-8')
        new_user = User(username=request.form.get('username'), password_hash=hashed_password, age=request.form.get('age'), birthplace=request.form.get('birthplace'))
        team_to_manage.manager = new_user
        db.session.add(new_user); db.session.add(team_to_manage); db.session.commit()
        flash('Account created! Please log in.', 'success'); return redirect(url_for('login'))
    available_teams = Team.query.filter_by(user_id=None).order_by(Team.name).all()
    return render_template('register.html', available_teams=available_teams)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated: return redirect(url_for('dashboard'))
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form.get('username')).first()
        if user and bcrypt.check_password_hash(user.password_hash, request.form.get('password')):
            login_user(user, remember=True); return redirect(url_for('dashboard'))
        else: flash('Login unsuccessful.', 'danger')
    return render_template('login.html')

@app.route('/logout')
def logout():
    logout_user(); return redirect(url_for('landing_page'))

# --- In-Game Routes ---
@app.route('/dashboard')
@login_required
def dashboard():
    user_team = current_user.team
    if not user_team: flash("You are not managing a team.", "warning"); return redirect(url_for('logout'))
    all_teams = Team.query.order_by(Team.points.desc(), (Team.goals_for - Team.goals_against).desc(), Team.goals_for.desc()).all()
    return render_template('dashboard.html', user_team=user_team, all_teams=all_teams)

@app.route('/next-fixture')
@login_required
def next_fixture():
    # ... (Same as before)
    current_round_state = GameState.query.filter_by(key='current_round').first()
    if current_round_state:
        new_round = int(current_round_state.value) + 1
        current_round_state.value = str(new_round)
        db.session.commit()
    return redirect(url_for('match_day'))

@app.route('/match-day')
@login_required
def match_day():
    # ... (Same as before)
    current_round_state = GameState.query.filter_by(key='current_round').first()
    current_round = int(current_round_state.value) if current_round_state else 1
    matches_this_round = Match.query.filter_by(round=current_round).all()
    team_count = Team.query.count()
    total_rounds = (team_count - 1) * 2 if team_count > 0 else 0
    all_rounds_played = current_round > total_rounds
    return render_template('index.html', matches=matches_this_round, current_round=current_round, all_rounds_played=all_rounds_played)

@app.route('/competitions')
@login_required
def competitions():
    # ... (Same as before)
    teams = Team.query.order_by(Team.points.desc(), (Team.goals_for - Team.goals_against).desc(), Team.goals_for.desc()).all()
    all_matches = Match.query.order_by(Match.round, Match.id).all()
    fixtures = {r: [m for m in all_matches if m.round == r] for r in range(1, 23)}
    top_scorers = Player.query.order_by(Player.goals_season.desc()).limit(10).all()
    return render_template('competitions.html', teams=teams, fixtures=fixtures, top_scorers=top_scorers, user_team=current_user.team)

@app.route('/all-teams')
@login_required
def all_teams():
    # ... (Same as before)
    teams = Team.query.order_by(Team.name).all()
    return render_template('all_teams.html', teams=teams, user_team=current_user.team)

@app.route('/player/<int:player_id>')
@login_required
def player_details(player_id):
    # ... (Same as before)
    player = Player.query.get_or_404(player_id)
    return render_template('player.html', player=player)

# --- SocketIO Handlers (Unchanged) ---
# ...

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        setup_database()
    socketio.run(app, debug=True)

