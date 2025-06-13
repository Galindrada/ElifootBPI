from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Team(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    hometown = db.Column(db.String(100), nullable=False)
    foundation_year = db.Column(db.Integer, nullable=False)
    stadium_capacity = db.Column(db.Integer, nullable=False)
    money = db.Column(db.Integer, default=5000000)
    
    # League Stats
    points = db.Column(db.Integer, default=0)
    games_played = db.Column(db.Integer, default=0)
    wins = db.Column(db.Integer, default=0)
    draws = db.Column(db.Integer, default=0)
    losses = db.Column(db.Integer, default=0)
    goals_for = db.Column(db.Integer, default=0)
    goals_against = db.Column(db.Integer, default=0)
    
    # FIX: Changed lazy='dynamic' to lazy=True (the default) to allow templates to iterate over players.
    players = db.relationship('Player', backref='team', lazy=True, cascade="all, delete-orphan")

class Player(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    position = db.Column(db.String(3), nullable=False)
    skill = db.Column(db.Integer, nullable=False)
    team_id = db.Column(db.Integer, db.ForeignKey('team.id'), nullable=False)

    attack = db.Column(db.Integer, default=50)
    defense = db.Column(db.Integer, default=50)
    power = db.Column(db.Integer, default=50)
    shot = db.Column(db.Integer, default=50)
    set_pieces = db.Column(db.Integer, default=50)

    games_played_season = db.Column(db.Integer, default=0)
    goals_season = db.Column(db.Integer, default=0)
    assists_season = db.Column(db.Integer, default=0)

class Match(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    round = db.Column(db.Integer, nullable=False)
    home_team_id = db.Column(db.Integer, db.ForeignKey('team.id'), nullable=False)
    away_team_id = db.Column(db.Integer, db.ForeignKey('team.id'), nullable=False)
    home_score = db.Column(db.Integer, nullable=True)
    away_score = db.Column(db.Integer, nullable=True)
    played = db.Column(db.Boolean, default=False)
    
    home_team = db.relationship('Team', foreign_keys=[home_team_id])
    away_team = db.relationship('Team', foreign_keys=[away_team_id])

class GameState(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(50), unique=True, nullable=False)
    value = db.Column(db.String(50), nullable=False)

