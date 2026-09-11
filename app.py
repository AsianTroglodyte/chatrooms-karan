import os
import random
import re
from datetime import datetime, timezone

from flask import Flask, flash, redirect, render_template, request, session, url_for
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func

db = SQLAlchemy()
migrate = Migrate()

ADJECTIVES = ["Blue", "Bright", "Calm", "Clever", "Kind", "Quick", "Quiet", "Red", "Silver", "Sunny"]
ANIMALS = ["Badger", "Bear", "Fox", "Hawk", "Koala", "Lion", "Otter", "Panda", "Tiger", "Wolf"]


class Room(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False, unique=True)
    created_by = db.Column(db.String(64), nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    messages = db.relationship("Message", backref="room", lazy=True, cascade="all, delete-orphan")


class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    room_id = db.Column(db.Integer, db.ForeignKey("room.id", ondelete="CASCADE"), nullable=False, index=True)
    author = db.Column(db.String(64), nullable=False)
    content = db.Column(db.Text, nullable=False)
    posted_at = db.Column(db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), index=True)


def create_app():
    app = Flask(__name__)
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        raise RuntimeError("DATABASE_URL must be set")
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)
    app.config.update(
        SECRET_KEY=os.environ.get("SECRET_KEY", "change-this-secret-key"),
        SQLALCHEMY_DATABASE_URI=database_url,
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
    )
    db.init_app(app)
    migrate.init_app(app, db)

    @app.before_request
    def assign_nickname():
        if "nickname" not in session:
            session["nickname"] = f"{random.choice(ADJECTIVES)}{random.choice(ANIMALS)}{random.randrange(100):02d}"

    @app.get("/")
    def index():
        rooms = (
            db.session.query(Room, func.count(Message.id).label("message_count"), func.coalesce(func.max(Message.posted_at), Room.created_at).label("last_activity"))
            .outerjoin(Message).group_by(Room.id)
            .order_by(func.coalesce(func.max(Message.posted_at), Room.created_at).desc()).all()
        )
        return render_template("index.html", rooms=rooms)

    @app.post("/rooms")
    def create_room():
        name = request.form.get("name", "").strip()
        if not name or len(name) > 120 or not re.search(r"\S", name):
            flash("Room names must contain 1–120 characters.", "error")
            return redirect(url_for("index"))
        if db.session.scalar(db.select(Room).where(func.lower(Room.name) == name.lower())):
            flash("That room already exists.", "error")
            return redirect(url_for("index"))
        room = Room(name=name, created_by=session["nickname"])
        db.session.add(room)
        db.session.commit()
        return redirect(url_for("room", room_id=room.id))

    @app.route("/rooms/<int:room_id>", methods=["GET", "POST"])
    def room(room_id):
        current_room = db.get_or_404(Room, room_id)
        if request.method == "POST":
            content = request.form.get("content", "").strip()
            if not content or len(content) > 2000:
                flash("Messages must contain 1–2,000 characters.", "error")
            else:
                db.session.add(Message(room_id=current_room.id, author=session["nickname"], content=content))
                db.session.commit()
                return redirect(url_for("room", room_id=current_room.id))
        messages = db.session.scalars(db.select(Message).where(Message.room_id == current_room.id).order_by(Message.posted_at.desc()).limit(50)).all()
        return render_template("room.html", room=current_room, messages=list(reversed(messages)))

    return app


app = create_app()
