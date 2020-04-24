import os

from flask import Flask, session, render_template, request, redirect, flash, jsonify
from flask_session.__init__ import Session
from flask_socketio import SocketIO, emit
from models import *

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

from werkzeug.security import check_password_hash, generate_password_hash

from helpers import login_required

app = Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"

app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")

Session(app)
socketio = SocketIO(app)

db.init_app(app)

engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))

messages_cache = {}
votes = {"yes": 0, "no": 0, "maybe": 0}

# '/' redirects users to the main chat room if they are signed in.
# otherwise, redirects user to signup
@app.route("/")
def index():
    if session.get("username") is None:
        return redirect("/login")
    else:
        return redirect("channels/general")


# '/login' manages login and redirects users to the main chat if they signed in.
@app.route("/login", methods=["GET", "POST"])
def login():
    session.clear()
    errors = []

    if request.method == "POST":
        username = request.form.get("username").strip()

        if not username:
            errors.append("Must provide username")
        if not request.form.get("password"):
            errors.append("Must provide password")

        user = User.query.filter(User.username==username).first()
        if user is None or not check_password_hash(user.password, request.form.get("password")):
            errors.append("Invalid password and/or username.")

        if not errors:
            session["username"] = username
            return redirect("/")

    return render_template("login.html", errors=errors)


#'/logout' helps user sign out
@app.route("/logout", methods=["GET", "POST"])
def logout():
    session.clear()
    return redirect("/")


# '/signup' handles signup activity and inserts new users into DB
@app.route("/signup", methods=["GET", "POST"])
def signup():
    session.clear()
    errors = []

    if request.method == "POST":
        username = request.form.get("username")
        gender = request.form.get("gender")

        if not username:
            errors.append("Must provide username")
        if not request.form.get("password"):
            errors.append("Must provide password")
        if not gender:
            errors.append("Must provide gender")

        if User.query.filter(User.username==username).first() is not None:
            errors.append("Username unavailable, please pick another one.")

        if request.form.get("password") != request.form.get("confirm_password"):
            errors.append("Passwords didn't match.")

        hashedPassword = generate_password_hash(
            request.form.get("password"),
            method='pbkdf2:sha256',
            salt_length=8
        )

        if not errors:
            User.add_user(username=username, password=hashedPassword, gender=gender)
            return redirect("/login")

    return render_template("signup.html", errors=errors)


# '/channels/<channel_name>' displays the message board for the chossen channel
@app.route("/channels/<string:channel_name>", methods=["GET", "POST"])
@login_required
def chat_board(channel_name):
    errors = []

    if Channel.query.filter(channel_name==channel_name).first() is None:
        errors.append(f"<{channel_name}> channel is not found.")

    # sync server chat history with DB chat history
    lazy_build_chat_history(channel_name, messages_cache)

    messages = []

    for object in messages_cache[channel_name]:
        messages.append(message_obj_to_string(object))

    channel_list = [channel.channel_name for channel in Channel.query.all()]

    return render_template(
        "chat_board.html",
        messages=messages,
        channels=channel_list,
        selected_channel=channel_name,
        errors=errors,
        votes=votes
    )


@app.route("/new/channel", methods=["POST"])
@login_required
def new_channel():

    channel_name = request.form.get('channel_name')
    if not channel_name:
        return jsonify({'success': False})

    try:
        Channel.add_channel(sanitize(channel_name))
        return jsonify({'success': True})
    except:
        return jsonify({'success': False})


@app.route("/list/channel", methods=["POST"])
@login_required
def list_channels():

    channels = []

    queries = Channel.query.all()
    for channel in queries:
        channels.append(channel.channel_name)

    return jsonify({'success': True, 'channels': channels})


# socketio action to add message to the data base and emit the change.
@socketio.on("add message")
def add_message(data):
    channel_name = data['channel_name']
    content = data['new_message']

    print(f"{content} posted to {channel_name}")

    message_obj = Message.add_message(
        content=content,
        username=session["username"],
        channel_name=channel_name,
        time="N/A"
    )

    # sync server chat history with DB chat history
    lazy_build_chat_history(channel_name, messages_cache, new_message=message_obj)

    message = message_obj_to_string(message_obj)

    emit("announce message", {"selection": message}, broadcast=True)


#lasy build the chat history for one channel from server
def lazy_build_chat_history(channel_name, messages_cache, new_message=None):
    if channel_name not in messages_cache:
        queries = Message.query.filter(Message.channel_name==channel_name).all()
        messages_cache[channel_name] = queries

    if new_message is not None:
        messages_cache[channel_name].append(new_message)

# Convert messages object list into plain text object
def message_obj_to_string(message_obj):
    return message_obj.username + ": " + message_obj.content


@socketio.on("submit vote")
def vote(data):
    selection = data["selection"]
    votes[selection] += 1
    emit("vote totals", votes, broadcast=True)


def sanitize(input):
    return '_'.join(input.split()).lower()
