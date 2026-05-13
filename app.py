import csv
import os
from datetime import datetime

from flask import Flask, render_template

app = Flask(__name__)

CSV_PATH = os.path.join(os.path.dirname(__file__), "Tentative Routine - Sheet2.csv")

ACTIVITY_COLORS = {
    "School": "#4A90D9",
    "Rai": "#E67E22",
    "Curiocity": "#2ECC71",
    "Mindmax": "#9B59B6",
    "Azmain": "#E74C3C",
    "May 27 batch": "#1ABC9C",
}

DAYS = ["Saturday", "Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]


def parse_csv():
    rows = []
    with open(CSV_PATH, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            start = row.get("Start", "").strip()
            end = row.get("End", "").strip()
            if not start or not end:
                continue
            slots = {}
            for day in DAYS:
                val = row.get(day, "").strip()
                slots[day] = val if val else ""
            rows.append({"start": start, "end": end, "slots": slots})
    return rows


def build_merge_map(schedule):
    """For each day, compute rowspan merges for consecutive identical activities."""
    merge = {}  # merge[(row_idx, day)] = {'rowspan': n, 'render': bool, 'start': str, 'end': str}
    for day in DAYS:
        i = 0
        while i < len(schedule):
            activity = schedule[i]["slots"][day]
            if activity:
                span = 1
                while (i + span < len(schedule)
                       and schedule[i + span]["slots"][day] == activity):
                    span += 1
                merge[(i, day)] = {
                    "rowspan": span,
                    "render": True,
                    "start": schedule[i]["start"],
                    "end": schedule[i + span - 1]["end"],
                }
                for k in range(1, span):
                    merge[(i + k, day)] = {"rowspan": 0, "render": False}
                i += span
            else:
                merge[(i, day)] = {"rowspan": 1, "render": True}
                i += 1
    return merge


def current_day_and_slot():
    now = datetime.now()
    day_map = {
        5: "Saturday",
        6: "Sunday",
        0: "Monday",
        1: "Tuesday",
        2: "Wednesday",
        3: "Thursday",
        4: "Friday",
    }
    current_day = day_map.get(now.weekday(), "")
    return current_day, now


@app.route("/")
def index():
    schedule = parse_csv()
    merge = build_merge_map(schedule)
    current_day, now = current_day_and_slot()
    return render_template(
        "index.html",
        schedule=schedule,
        days=DAYS,
        colors=ACTIVITY_COLORS,
        current_day=current_day,
        now=now,
        merge=merge,
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
