from flask import Flask, render_template, redirect, url_for, flash, request, session, g
from flask_socketio import SocketIO, emit
from sqlalchemy import desc, text
from models import db, User, Team, Player, Match, GameState
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
import os
import random
from time import sleep
from flask_socketio import disconnect
import shutil
import time
from sqlalchemy.orm import joinedload

# --- App Configuration ---
app = Flask(__name__, instance_relative_config=True)
app.config['SECRET_KEY'] = 'a_very_secret_key_change_me'
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(app.instance_path, "elifoot_users.db")}'  # Central user DB
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Ensure instance folder exists
os.makedirs(app.instance_path, exist_ok=True)

# --- Extensions Initialization ---
db.init_app(app)
bcrypt = Bcrypt(app)
socketio = SocketIO(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# --- DB Path Helpers ---
def get_user_db_path(username):
    db_path = os.path.join(app.instance_path, f'elifoot_{username}.db')
    return f'sqlite:///{db_path}'

BASE_DB_PATH = os.path.join(app.instance_path, 'elifoot_base.db')
USERS_DB_PATH = os.path.join(app.instance_path, 'elifoot_users.db')

# --- Helper to initialize a new user's game DB ---
def initialize_user_game_db(username):
    user_db_path = f'elifoot_{username}.db'
    # Copy a template DB if you want, or run setup_database logic here
    # For now, we'll run setup_database on the new DB
    from sqlalchemy import create_engine
    from sqlalchemy.orm import scoped_session, sessionmaker
    engine = create_engine(f'sqlite:///{user_db_path}')
    from models import db as user_db
    user_db.session = scoped_session(sessionmaker(bind=engine))
    user_db.create_all()
    # Run the setup_database logic on this DB
    # Temporarily swap db.session to the new one
    old_session = db.session
    db.session = user_db.session
    setup_database()
    db.session = old_session

# --- Before Request: Set DB for logged-in user ---
@app.before_request
def before_request():
    if 'user_db' in session:
        app.config['SQLALCHEMY_DATABASE_URI'] = session['user_db']
    else:
        app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{USERS_DB_PATH}'
    db.session.remove()
    db.engine.dispose()
    db.session.expire_all()

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# --- Database Setup ---
def setup_database():
    db.create_all()  # Ensure all tables and columns exist before queries
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

# --- Function to create and initialize the base DB ---
def create_base_db():
    base_db_path = BASE_DB_PATH
    needs_init = False
    if not os.path.exists(base_db_path):
        needs_init = True
    else:
        from sqlalchemy import create_engine, inspect
        engine = create_engine(f'sqlite:///{base_db_path}')
        inspector = inspect(engine)
        if 'team' not in inspector.get_table_names():
            needs_init = True
    if not needs_init:
        return  # Already exists and is valid

    from sqlalchemy import create_engine
    engine = create_engine(f'sqlite:///{base_db_path}')
    from models import Team, Player, db
    db.metadata.create_all(engine)
    from sqlalchemy.orm import sessionmaker
    Session = sessionmaker(bind=engine)
    session = Session()
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
    import random
    player_names = ['Ana', 'Sofia', 'Maria', 'Leonor', 'Beatriz', 'Mariana', 'Carolina', 'Inês', 'Lara', 'Matilde']
    player_surnames = ['Silva', 'Santos', 'Ferreira', 'Pereira', 'Oliveira', 'Costa', 'Rodrigues', 'Martins']
    for data in teams_data:
        team = Team(**data, managed_by="CPU")
        session.add(team)
        session.flush()
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
            session.add(player)
    session.commit()
    session.close()

# --- Auth Routes ---
@app.route('/')
def landing_page():
    if current_user.is_authenticated: return redirect(url_for('dashboard'))
    return render_template('landing.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    create_base_db()  # Ensure base DB exists
    from sqlalchemy import create_engine
    from sqlalchemy.orm import scoped_session, sessionmaker
    base_engine = create_engine(f'sqlite:///{BASE_DB_PATH}')
    from models import Team as BaseTeam
    BaseSession = scoped_session(sessionmaker(bind=base_engine))
    available_teams = BaseSession.query(BaseTeam).filter(BaseTeam.managed_by == "CPU").order_by(BaseTeam.name).all()
    if request.method == 'POST':
        if User.query.filter_by(username=request.form.get('username')).first():
            flash('Username already exists.', 'danger'); return redirect(url_for('register'))
        team_id = request.form.get('team_id')
        if not team_id:
            flash('Please select a team.', 'danger'); return redirect(url_for('register'))
        hashed_password = bcrypt.generate_password_hash(request.form.get('password')).decode('utf-8')
        new_user = User(username=request.form.get('username'), password_hash=hashed_password, age=request.form.get('age'), birthplace=request.form.get('birthplace'))
        db.session.add(new_user)
        db.session.commit()
        user_db_path = os.path.join(app.instance_path, f'elifoot_{new_user.username}.db')
        shutil.copyfile(BASE_DB_PATH, user_db_path)
        user_engine = create_engine(f'sqlite:///{user_db_path}')
        from models import Team as UserTeam
        UserSession = scoped_session(sessionmaker(bind=user_engine))
        user_team = UserSession.query(UserTeam).get(int(team_id))
        user_team.managed_by = new_user.username
        print("Assigning team", user_team.name, "to user", new_user.username)
        print("managed_by after assignment:", user_team.managed_by)
        UserSession.commit()
        UserSession.close()
        UserSession.remove()
        import time
        time.sleep(0.1)
        session['user_db'] = get_user_db_path(new_user.username)
        flash('Account created! Please log in.', 'success'); return redirect(url_for('login'))
    return render_template('register.html', available_teams=available_teams)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated: return redirect(url_for('dashboard'))
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form.get('username')).first()
        if user and bcrypt.check_password_hash(user.password_hash, request.form.get('password')):
            login_user(user, remember=True)
            # Set the session to use the user's DB
            session['user_db'] = get_user_db_path(user.username)
            return redirect(url_for('dashboard'))
        else: flash('Login unsuccessful.', 'danger')
    return render_template('login.html')

@app.route('/logout')
def logout():
    logout_user()
    session.pop('user_db', None)
    return redirect(url_for('landing_page'))

# --- In-Game Routes ---
@app.route('/dashboard')
@login_required
def dashboard():
    import os
    db_path = os.path.join(app.instance_path, f'elifoot_{current_user.username}.db')
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from models import Team
    engine = create_engine(f'sqlite:///{db_path}')
    Session = sessionmaker(bind=engine)
    session = Session()
    user_team = session.query(Team).options(joinedload(Team.players)).filter_by(managed_by=current_user.username).first()
    print('Team found for this user (direct engine):', user_team)
    all_teams = session.query(Team).order_by(Team.points.desc(), (Team.goals_for - Team.goals_against).desc(), Team.goals_for.desc()).all()
    session.close()
    if not user_team:
        return render_template('dashboard.html', user_team=None, all_teams=[])
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
@socketio.on('start_fixture_simulation')
def handle_start_fixture_simulation(data=None):
    from sqlalchemy.orm import joinedload
    current_round_state = GameState.query.filter_by(key='current_round').first()
    if not current_round_state:
        emit('log_message', {'data': 'No current round found.'})
        return
    current_round = int(current_round_state.value)
    matches = Match.query.options(joinedload(Match.home_team), joinedload(Match.away_team)).filter_by(round=current_round, played=False).all()
    if not matches:
        emit('log_message', {'data': 'No matches to simulate for this round.'})
        emit('fixture_finished')
        return

    scores = {match.id: {'home': 0, 'away': 0} for match in matches}
    match_events = {match.id: [] for match in matches}
    goal_scorers = {match.id: {'home': [], 'away': []} for match in matches}
    minutes = 90
    for minute in range(1, minutes + 1):
        for match in matches:
            if random.random() < 0.04:  # ~4% chance of a goal per match per minute
                scoring_team = 'home' if random.random() < 0.5 else 'away'
                scores[match.id][scoring_team] += 1
                # Select a random player from the scoring team
                if scoring_team == 'home':
                    players = Player.query.filter_by(team_id=match.home_team_id).all()
                else:
                    players = Player.query.filter_by(team_id=match.away_team_id).all()
                if players:
                    scorer = random.choice(players)
                    scorer.goals_season += 1
                    db.session.commit()
                    event = f"{minute}' - Goal! {scorer.name} ({match.home_team.name if scoring_team == 'home' else match.away_team.name})"
                else:
                    event = f"{minute}' - Goal! {match.home_team.name if scoring_team == 'home' else match.away_team.name} (no player found)"
                match_events[match.id].append(event)
                emit('log_message', {'data': event})
        emit('minute_update', {'minute': minute, 'scores': scores})
        sleep(0.05)  # Short delay for realism (reduce if needed)

    # Update DB with results
    for match in matches:
        match.home_score = scores[match.id]['home']
        match.away_score = scores[match.id]['away']
        match.played = True
        # Update team stats
        match.home_team.goals_for += match.home_score
        match.home_team.goals_against += match.away_score
        match.away_team.goals_for += match.away_score
        match.away_team.goals_against += match.home_score
        match.home_team.games_played += 1
        match.away_team.games_played += 1
        if match.home_score > match.away_score:
            match.home_team.wins += 1
            match.home_team.points += 3
            match.away_team.losses += 1
        elif match.home_score < match.away_score:
            match.away_team.wins += 1
            match.away_team.points += 3
            match.home_team.losses += 1
        else:
            match.home_team.draws += 1
            match.away_team.draws += 1
            match.home_team.points += 1
            match.away_team.points += 1
    db.session.commit()
    emit('fixture_finished')

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        setup_database()
    socketio.run(app, debug=True)

