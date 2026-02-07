from flask import Flask, render_template, request, jsonify, session, redirect, url_for, send_from_directory
from flask_cors import CORS
import google.generativeai as genai
import pymysql
import os
import re
import json
from datetime import datetime, timedelta

# -------------------------------------------------
# App Configuration
# -------------------------------------------------
app = Flask(__name__)

app.secret_key = os.environ.get("FLASK_SECRET_KEY", "dummy_secret_key")
app.config["SESSION_COOKIE_NAME"] = "flask_session"
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(minutes=30)

# -------------------------------------------------
# CORS Configuration
# -------------------------------------------------
CORS(app, supports_credentials=True)

# -------------------------------------------------
# Database Configuration (USE ENV VARIABLES)
# -------------------------------------------------
db_config = {
    "host": os.environ.get("DB_HOST", "localhost"),
    "user": os.environ.get("DB_USER", "root"),
    "password": os.environ.get("DB_PASSWORD", ""),
    "database": os.environ.get("DB_NAME", "your_database"),
    "cursorclass": pymysql.cursors.DictCursor
}

def get_db_connection():
    return pymysql.connect(**db_config)

# -------------------------------------------------
# Gemini AI Configuration
# -------------------------------------------------
genai.configure(api_key=os.environ.get("GOOGLE_API_KEY", "DUMMY_API_KEY"))
model = genai.GenerativeModel("gemini-2.0-flash")

# -------------------------------------------------
# Routes
# -------------------------------------------------
@app.route("/")
def home():
    if "user_name" not in session:
        return redirect("http://localhost/hack/index.html")
    return render_template("chatbot.html")

@app.route("/php_login")
def php_login():
    user_name = request.args.get("user_name")
    redirect_page = request.args.get("redirect")

    if not user_name:
        return jsonify({"error": "Username required"}), 400

    session["user_name"] = user_name

    if redirect_page == "pricing":
        return redirect(url_for("pricing"))
    return redirect(url_for("home"))

@app.route("/pricing")
def pricing():
    if "user_name" not in session:
        return redirect("http://localhost/hack/index.html")
    return render_template("pricing.html")

@app.route("/get_username")
def get_username():
    if "user_name" in session:
        return jsonify({"username": session["user_name"]})
    return jsonify({"error": "Not logged in"}), 401

@app.route("/logout")
def logout():
    session.clear()
    return redirect("http://localhost/hack/index.html")

# -------------------------------------------------
# Chat API
# -------------------------------------------------
@app.route("/api/chat", methods=["POST"])
def chat():
    if "user_name" not in session:
        return jsonify({"error": "Not logged in"}), 401

    user_message = request.json.get("message", "").strip()
    if not user_message:
        return jsonify({"response": "Please enter a message."})

    prompt = f"""
    Generate optimized SQL queries based on user requests.
    If not related to SQL, reply politely.
    User: {user_message}
    """

    try:
        response = model.generate_content(prompt)
        ai_response = response.text.strip()

        sql_match = re.search(r"SQL:(.+)", ai_response, re.DOTALL)
        sql_query = sql_match.group(1).strip() if sql_match else None

        connection = get_db_connection()
        with connection.cursor() as cursor:
            cursor.execute("""
                INSERT INTO chat_history
                (username, user_message, ai_response, created_at)
                VALUES (%s, %s, %s, NOW())
            """, (session["user_name"], user_message, ai_response))
        connection.commit()
        connection.close()

        return jsonify({
            "response": ai_response,
            "sql": sql_query
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# -------------------------------------------------
# Chat History
# -------------------------------------------------
@app.route("/api/history")
def chat_history():
    if "user_name" not in session:
        return jsonify({"error": "Not logged in"}), 401

    connection = get_db_connection()
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT user_message, ai_response, created_at
            FROM chat_history
            WHERE username=%s
            ORDER BY created_at DESC
            LIMIT 100
        """, (session["user_name"],))
        history = cursor.fetchall()
    connection.close()

    return jsonify({"history": history})

# -------------------------------------------------
# Static Files
# -------------------------------------------------
@app.route("/static/<path:filename>")
def static_files(filename):
    return send_from_directory("static", filename)

# -------------------------------------------------
# Run Server
# -------------------------------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
