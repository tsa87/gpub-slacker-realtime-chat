from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = "users"
    username = db.Column(db.String, primary_key=True, nullable=False)
    password = db.Column(db.String, nullable=False)
    gender = db.Column(db.String, nullable=False)
    channel_names = db.relationship("Membership", backref="user", lazy=True)

    def add_user(username, password, gender):
        user = User(username=username, password=password, gender=gender)
        db.session.add(user)
        db.session.commit()

class Channel(db.Model):
    __tablename__ = "channels"
    channel_name = db.Column(db.String, primary_key=True, nullable=False)
    member_names = db.relationship("Membership", backref="channel", lazy=True)

    def add_channel(channel_name):
        channel = Channel(channel_name=channel_name)
        db.session.add(channel)
        db.session.commit()


class Membership(db.Model):
    __tablename__ = "memberships"
    username = db.Column(db.String, db.ForeignKey("users.username"), primary_key=True, nullable=False)
    channel_names = db.Column(db.String, db.ForeignKey("channels.channel_name"), primary_key=True, nullable=False)

class Message(db.Model):
    __tablename__ = "messages"
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String, nullable=False)
    username = db.Column(db.String, db.ForeignKey("users.username"), nullable=False)
    channel_name= db.Column(db.String, db.ForeignKey("channels.channel_name"), nullable=False)
    time = db.Column(db.String, nullable=False)

    def add_message(content, username, channel_name, time):
        message = Message(content=content, username=username, channel_name=channel_name, time=time)
        db.session.add(message)
        db.session.commit()

        return message
