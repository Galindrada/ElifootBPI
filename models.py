from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy()

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    birthplace = db.Column(db.String(100), nullable=False)
    # A user now directly manages one team. The backref allows team.manager
    team = db.relationship('Team', backref='manager', uselist=False)

class Team(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    hometown = db.Column(db.String(100), nullable=False)
    foundation_year = db.Column(db.Integer, nullable=False)
    stadium_capacity = db.Column(db.Integer, nullable=False)
    money = db.Column(db.Integer, default=5000000)
    # Foreign key to link to a user. Must be unique so only one user can manage a team.
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True, unique=True)
    
    points = db.Column(db.Integer, default=0)
    games_played = db.Column(db.Integer, default=0)
    wins = db.Column(db.Integer, default=0)
    draws = db.Column(db.Integer, default=0)
    losses = db.Column(db.Integer, default=0)
    goals_for = db.Column(db.Integer, default=0)
    goals_against = db.Column(db.Integer, default=0)
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

class GameState(db.Model): # FIX: Changed db.model to db.Model
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(50), unique=True, nullable=False)
    value = db.Column(db.String(50), nullable=False)

