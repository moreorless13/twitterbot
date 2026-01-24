from flask import Flask, jsonify
from db import get_db_connection  # assuming the helper is in db.py

app = Flask(__name__)
# app.config updates for DB_* values go here if you prefer config variables

@app.route("/users")
def list_users():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, name FROM users")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    users = [{"id": row[0], "name": row[1]} for row in rows]
    return jsonify(users)
