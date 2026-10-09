import os
import sqlite3
from datetime import date
from pathlib import Path

from flask import Flask, redirect, render_template, request, url_for

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024

DATA_DIR = Path(os.environ.get("DATA_DIR", "data"))
DATA_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = DATA_DIR / "planner.db"


def connect_db():
    connection = sqlite3.connect(DB_PATH, timeout=10)
    connection.row_factory = sqlite3.Row
    return connection


with connect_db() as db:
    db.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            subject TEXT NOT NULL,
            due_date TEXT NOT NULL,
            priority TEXT NOT NULL,
            completed INTEGER NOT NULL DEFAULT 0
        )
    """)


def show_dashboard(error=None, status=200):
    with connect_db() as db:
        tasks = db.execute("""
            SELECT * FROM tasks
            ORDER BY completed ASC, due_date ASC, id DESC
        """).fetchall()

    total = len(tasks)
    completed = sum(task["completed"] for task in tasks)
    today = date.today().isoformat()
    overdue = sum(
        not task["completed"] and task["due_date"] < today
        for task in tasks
    )

    return render_template(
        "index.html",
        tasks=tasks,
        total=total,
        completed=completed,
        pending=total - completed,
        overdue=overdue,
        progress=round(completed / total * 100) if total else 0,
        today=today,
        error=error,
    ), status


@app.get("/")
def index():
    return show_dashboard()


@app.post("/tasks")
def add_task():
    title = request.form.get("title", "").strip()
    subject = request.form.get("subject", "").strip()
    due_date = request.form.get("due_date", "").strip()
    priority = request.form.get("priority", "").strip()

    if not title or len(title) > 100:
        return show_dashboard(
            "Enter a task title between 1 and 100 characters.", 400
        )

    if not subject or len(subject) > 60:
        return show_dashboard(
            "Enter a subject between 1 and 60 characters.", 400
        )

    try:
        parsed_date = date.fromisoformat(due_date)
    except ValueError:
        return show_dashboard("Enter a valid due date.", 400)

    if priority not in {"Low", "Medium", "High"}:
        return show_dashboard("Choose a valid priority.", 400)

    with connect_db() as db:
        db.execute(
            """
            INSERT INTO tasks (title, subject, due_date, priority)
            VALUES (?, ?, ?, ?)
            """,
            (title, subject, parsed_date.isoformat(), priority),
        )

    return redirect(url_for("index"), code=303)


@app.post("/tasks/<int:task_id>/toggle")
def toggle_task(task_id):
    with connect_db() as db:
        result = db.execute(
            """
            UPDATE tasks
            SET completed = 1 - completed
            WHERE id = ?
            """,
            (task_id,),
        )
        if result.rowcount == 0:
            return show_dashboard("That task could not be found.", 404)

    return redirect(url_for("index"), code=303)


@app.get("/health")
def health():
    with connect_db() as db:
        db.execute("SELECT COUNT(*) FROM tasks").fetchone()
    return {"status": "ok"}, 200