from flask import Flask, render_template, redirect, url_for, abort
from flask_socketio import SocketIO, emit
from sqlalchemy import desc, func
from models import db, Team, Player, Match, GameState
import time
import random

app = Flask(__name__)
app.config['SECRET_KEY'] = 'a_very_secret_key_change_me'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///game.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
socketio = SocketIO(app)

# --- Routes ---
@app.route('/')
def index():
    """Serve the Match Day page."""
    current_round_state = GameState.query.filter_by(key='current_round').first()
    if not current_round_state:
        return render_template('index.html', matches=[], current_round=0, all_rounds_played=False)

    current_round = int(current_round_state.value)
    matches_this_round = Match.query.filter_by(round=current_round).all()
    
    total_rounds = (Team.query.count() - 1) * 2 if Team.query.count() > 0 else 0
    all_rounds_played = current_round > total_rounds

    return render_template('index.html', matches=matches_this_round, current_round=current_round, all_rounds_played=all_rounds_played)

@app.route('/competitions')
def competitions():
    """Display league table, fixtures, and top scorers."""
    teams = Team.query.all()
    teams.sort(key=lambda x: (x.points, x.goals_for - x.goals_against, x.goals_for), reverse=True)

    all_matches = Match.query.order_by(Match.round, Match.id).all()
    fixtures_by_round = {}
    for match in all_matches:
        if match.round not in fixtures_by_round:
            fixtures_by_round[match.round] = []
        fixtures_by_round[match.round].append(match)

    # Query for top 10 goalscorers
    top_scorers = Player.query.order_by(Player.goals_season.desc()).limit(10).all()
        
    return render_template('competitions.html', teams=teams, fixtures=fixtures_by_round, top_scorers=top_scorers)

@app.route('/all-teams')
def all_teams():
    """Display all teams and their players."""
    teams = Team.query.order_by(Team.name).all()
    return render_template('all_teams.html', teams=teams)

@app.route('/player/<int:player_id>')
def player_details(player_id):
    """Display the detailed screen for a single player."""
    player = Player.query.get_or_404(player_id)
    return render_template('player.html', player=player)

@app.route('/next-fixture')
def next_fixture():
    """Advance the game to the next round."""
    current_round_state = GameState.query.filter_by(key='current_round').first()
    if current_round_state:
        new_round = int(current_round_state.value) + 1
        current_round_state.value = str(new_round)
        db.session.commit()
    return redirect(url_for('index'))

@app.route('/populate-db')
def populate_db():
    # ... (This function remains the same as your version)
    db.drop_all()
    db.create_all()
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
    teams_list = []
    for data in teams_data:
        team = Team(**data)
        db.session.add(team)
        teams_list.append(team)
    db.session.commit()
    player_names = ['Ana', 'Sofia', 'Maria', 'Leonor', 'Beatriz', 'Mariana', 'Carolina', 'Inês', 'Lara', 'Matilde']
    player_surnames = ['Silva', 'Santos', 'Ferreira', 'Pereira', 'Oliveira', 'Costa', 'Rodrigues', 'Martins']
    for team in teams_list:
        player_names_in_team = set()
        for i in range(22):
            full_name = f"{random.choice(player_names)} {random.choice(player_surnames)}"
            while full_name in player_names_in_team:
                full_name = f"{random.choice(player_names)} {random.choice(player_surnames)}"
            player_names_in_team.add(full_name)
            pos = 'GK' if i < 2 else 'DF' if i < 8 else 'MF' if i < 15 else 'FW'
            player = Player(name=full_name, age=random.randint(18, 34), position=pos, skill=random.randint(40, 85), team_id=team.id, attack=random.randint(30,90), defense=random.randint(30,90), power=random.randint(30,90), shot=random.randint(30,90), set_pieces=random.randint(30,90))
            db.session.add(player)
    generate_round_robin_fixtures(teams_list)
    db.session.add(GameState(key='current_round', value='1'))
    db.session.commit()
    return redirect(url_for('competitions'))


# --- Helper Functions ---
def generate_round_robin_fixtures(teams):
    # ... (This function remains the same)
    local_teams = list(teams)
    if len(local_teams) % 2 != 0:
        local_teams.append(None)
    n = len(local_teams)
    schedule = []
    for i in range(n - 1):
        round_fixtures = []
        for j in range(n // 2):
            home, away = local_teams[j], local_teams[n - 1 - j]
            if home and away:
                round_fixtures.append((home, away))
        schedule.append(round_fixtures)
        local_teams.insert(1, local_teams.pop())
    for round_num, round_fixtures in enumerate(schedule, 1):
        for home_team, away_team in round_fixtures:
            match = Match(round=round_num, home_team_id=home_team.id, away_team_id=away_team.id)
            db.session.add(match)
    total_rounds = n - 1
    for round_num, round_fixtures in enumerate(schedule, 1):
        for home_team, away_team in round_fixtures:
            match = Match(round=round_num + total_rounds, home_team_id=away_team.id, away_team_id=home_team.id)
            db.session.add(match)

def get_team_strength(team, area):
    """Calculates a team's strength in 'attack' or 'defense'."""
    if area == 'attack':
        # Average attack skill of midfielders and forwards
        players = Player.query.filter(Player.team_id == team.id, Player.position.in_(['MF', 'FW'])).all()
        return sum(p.attack for p in players) / len(players) if players else 50
    if area == 'defense':
        # Average defense skill of defenders and midfielders
        players = Player.query.filter(Player.team_id == team.id, Player.position.in_(['DF', 'MF'])).all()
        return sum(p.defense for p in players) / len(players) if players else 50
    return 50


# --- SocketIO Handlers ---
@socketio.on('connect')
def handle_connect():
    emit('log_message', {'data': 'Connected to the simulation server.'})

@socketio.on('start_fixture_simulation')
def handle_start_fixture(json):
    """Simulates all matches for the current round, minute by minute."""
    current_round_state = GameState.query.filter_by(key='current_round').first()
    if not current_round_state: return

    current_round = int(current_round_state.value)
    matches_to_play = Match.query.filter_by(round=current_round, played=False).all()

    if not matches_to_play:
        emit('log_message', {'data': 'This fixture has already been played.'})
        emit('fixture_finished')
        return

    emit('log_message', {'data': f'--- Simulating Fixture {current_round} ---'})
    
    # Initialize live scores for all matches this round
    live_scores = {m.id: {'home': 0, 'away': 0} for m in matches_to_play}

    for minute in range(1, 91):
        for match in matches_to_play:
            # --- Simple Goal Probability Logic ---
            home_attack = get_team_strength(match.home_team, 'attack')
            away_defense = get_team_strength(match.away_team, 'defense')
            away_attack = get_team_strength(match.away_team, 'attack')
            home_defense = get_team_strength(match.home_team, 'defense')

            # Probability per minute, scaled down. Base chance + advantage
            home_goal_prob = 0.015 + (home_attack - away_defense) / 2000.0
            away_goal_prob = 0.015 + (away_attack - home_defense) / 2000.0

            if random.random() < home_goal_prob:
                live_scores[match.id]['home'] += 1
                # Assign goal to a player
                scorer = Player.query.filter(Player.team_id == match.home_team_id, Player.position.in_(['MF', 'FW'])).order_by(func.random()).first()
                if scorer:
                    scorer.goals_season += 1
                    db.session.add(scorer)
                    emit('log_message', {'data': f"GOAL! {minute}' - {scorer.name} ({match.home_team.name})"})
            
            if random.random() < away_goal_prob:
                live_scores[match.id]['away'] += 1
                # Assign goal to a player
                scorer = Player.query.filter(Player.team_id == match.away_team_id, Player.position.in_(['MF', 'FW'])).order_by(func.random()).first()
                if scorer:
                    scorer.goals_season += 1
                    db.session.add(scorer)
                    emit('log_message', {'data': f"GOAL! {minute}' - {scorer.name} ({match.away_team.name})"})

        emit('minute_update', {'minute': minute, 'scores': live_scores})
        socketio.sleep(0.1) # Speed of simulation

    # Finalize match results and team stats
    for match in matches_to_play:
        final_score = live_scores[match.id]
        match.home_score = final_score['home']
        match.away_score = final_score['away']
        match.played = True
        db.session.add(match)
        
        # Update team stats
        home_team, away_team = match.home_team, match.away_team
        home_team.games_played += 1; away_team.games_played += 1
        home_team.goals_for += match.home_score; away_team.goals_for += match.away_score
        home_team.goals_against += match.away_score; away_team.goals_against += match.home_score
        
        if match.home_score > match.away_score:
            home_team.wins += 1; home_team.points += 3; away_team.losses += 1
        elif match.away_score > match.home_score:
            away_team.wins += 1; away_team.points += 3; home_team.losses += 1
        else:
            home_team.draws += 1; away_team.draws += 1; home_team.points += 1; away_team.points += 1
        
        # Update games played for all players
        for player in home_team.players: player.games_played_season += 1
        for player in away_team.players: player.games_played_season += 1
            
        db.session.add(home_team)
        db.session.add(away_team)

    db.session.commit()
    emit('log_message', {'data': '--- Fixture Finished ---'})
    emit('fixture_finished')


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    socketio.run(app, debug=True)


