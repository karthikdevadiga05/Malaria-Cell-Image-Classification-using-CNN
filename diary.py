from flask import Blueprint, render_template, request, redirect, url_for, session
import sqlite3

diary_bp = Blueprint('diary', __name__)

def get_db():
    conn = sqlite3.connect('users.db')
    conn.row_factory = sqlite3.Row
    return conn

@diary_bp.route("/diary")
def diary_home():
    if 'username' not in session:
        return redirect(url_for('login'))

    title_query = request.args.get("title", "").strip()
    date_query = request.args.get("date", "").strip()

    query = "SELECT * FROM diary WHERE username = ?"
    params = [session['username']]

    if title_query:
        query += " AND title LIKE ?"
        params.append(f"%{title_query}%")
    if date_query:
        query += " AND DATE(timestamp) = ?"
        params.append(date_query)

    conn = get_db()
    entries = conn.execute(query, params).fetchall()
    conn.close()

    return render_template("diary.html", entries=entries, is_search=bool(title_query or date_query))

@diary_bp.route("/add", methods=["POST"])
def add():
    if 'username' not in session:
        return redirect(url_for('login'))

    title = request.form["title"]
    content = request.form["content"]

    conn = get_db()
    conn.execute("INSERT INTO diary (username, title, content) VALUES (?, ?, ?)",
                 (session['username'], title, content))
    conn.commit()
    conn.close()

    return redirect(url_for("diary.diary_home"))

@diary_bp.route("/delete/<int:entry_id>")
def delete(entry_id):
    if 'username' not in session:
        return redirect(url_for('login'))

    conn = get_db()
    conn.execute("DELETE FROM diary WHERE id = ? AND username = ?", (entry_id, session['username']))
    conn.commit()
    conn.close()

    return redirect(url_for("diary.diary_home"))
