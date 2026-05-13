import csv
import json
import os
from datetime import datetime
from functools import wraps

from flask import Flask, jsonify, render_template, request, session, redirect, url_for

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", os.urandom(24).hex())

APP_PASSWORD = os.environ.get("APP_PASSWORD", "default")

BASE_DIR = os.path.dirname(__file__)
CSV_PATH = os.path.join(BASE_DIR, "Tentative Routine - Sheet2.csv")
JSON_PATH = os.path.join(BASE_DIR, "schedule.json")

ACTIVITY_COLORS = {
    "School": "#4A90D9",
    "Rai": "#E67E22",
    "Curiocity": "#2ECC71",
    "Mindmax": "#9B59B6",
    "Azmain": "#E74C3C",
    "May 27 batch": "#1ABC9C",
}

DAYS = ["Saturday", "Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]

TIME_SLOTS = [
    ("8:00 AM", "8:30 AM"), ("8:30 AM", "9:00 AM"), ("9:00 AM", "9:30 AM"),
    ("9:30 AM", "10:00 AM"), ("10:00 AM", "10:30 AM"), ("10:30 AM", "11:00 AM"),
    ("11:00 AM", "11:30 AM"), ("11:30 AM", "12:00 PM"), ("12:00 PM", "12:30 PM"),
    ("12:30 PM", "1:00 PM"), ("1:00 PM", "1:30 PM"), ("1:30 PM", "2:00 PM"),
    ("2:00 PM", "2:30 PM"), ("2:30 PM", "3:00 PM"), ("3:00 PM", "3:30 PM"),
    ("3:30 PM", "4:00 PM"), ("4:00 PM", "4:30 PM"), ("4:30 PM", "5:00 PM"),
    ("5:00 PM", "5:30 PM"), ("5:30 PM", "6:00 PM"), ("6:00 PM", "6:30 PM"),
    ("6:30 PM", "7:00 PM"), ("7:00 PM", "7:30 PM"), ("7:30 PM", "8:00 PM"),
    ("8:00 PM", "8:30 PM"), ("8:30 PM", "9:00 PM"), ("9:00 PM", "9:30 PM"),
    ("9:30 PM", "10:00 PM"), ("10:00 PM", "10:30 PM"), ("10:30 PM", "11:00 PM"),
    ("11:00 PM", "11:30 PM"), ("11:30 PM", "12:00 AM"),
]


def load_schedule():
    """Load schedule from JSON, falling back to CSV import."""
    if os.path.exists(JSON_PATH):
        with open(JSON_PATH, "r") as f:
            return json.load(f)

    # First run: import from CSV
    schedule = {}
    for day in DAYS:
        schedule[day] = {}
        for start, end in TIME_SLOTS:
            schedule[day][start] = ""

    if os.path.exists(CSV_PATH):
        with open(CSV_PATH, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                start = row.get("Start", "").strip()
                for day in DAYS:
                    val = row.get(day, "").strip()
                    if val and start in schedule.get(day, {}):
                        schedule[day][start] = val

    save_schedule(schedule)
    return schedule


def save_schedule(schedule):
    with open(JSON_PATH, "w") as f:
        json.dump(schedule, f, indent=2)


def current_day():
    day_map = {
        5: "Saturday", 6: "Sunday", 0: "Monday",
        1: "Tuesday", 2: "Wednesday", 3: "Thursday", 4: "Friday",
    }
    return day_map.get(datetime.now().weekday(), "")


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("authenticated"):
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated


@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        if request.form.get("password") == APP_PASSWORD:
            session["authenticated"] = True
            return redirect(url_for("index"))
        error = "Wrong password"
    return render_template("login.html", error=error)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/")
@login_required
def index():
    return render_template(
        "index.html",
        days=DAYS,
        time_slots=TIME_SLOTS,
        colors=ACTIVITY_COLORS,
        current_day=current_day(),
    )


@app.route("/api/schedule")
@login_required
def get_schedule():
    return jsonify(load_schedule())


@app.route("/api/schedule", methods=["POST"])
@login_required
def update_slot():
    data = request.get_json()
    day = data.get("day")
    time_slot = data.get("time")
    activity = data.get("activity", "").strip()

    if day not in DAYS:
        return jsonify({"error": "Invalid day"}), 400

    valid_times = [t[0] for t in TIME_SLOTS]
    if time_slot not in valid_times:
        return jsonify({"error": "Invalid time slot"}), 400

    schedule = load_schedule()
    schedule[day][time_slot] = activity
    save_schedule(schedule)
    return jsonify({"ok": True})


@app.route("/api/schedule/move", methods=["POST"])
@login_required
def move_slot():
    data = request.get_json()
    src_day = data.get("srcDay")
    src_time = data.get("srcTime")
    dst_day = data.get("dstDay")
    dst_time = data.get("dstTime")

    if src_day not in DAYS or dst_day not in DAYS:
        return jsonify({"error": "Invalid day"}), 400

    schedule = load_schedule()
    activity = schedule.get(src_day, {}).get(src_time, "")
    if not activity:
        return jsonify({"error": "No activity at source"}), 400

    schedule[src_day][src_time] = ""
    schedule[dst_day][dst_time] = activity
    save_schedule(schedule)
    return jsonify({"ok": True})


@app.route("/api/colors")
@login_required
def get_colors():
    return jsonify(ACTIVITY_COLORS)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
