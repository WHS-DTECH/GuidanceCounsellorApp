import os
from flask import Flask, render_template_string, request, redirect, session, url_for
from database import StudentBackend

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "dev-secret-key")
app.config["PREFERRED_URL_SCHEME"] = "https"

backend = StudentBackend()

HTML_TEMPLATE = """
<!doctype html>
<html>
  <head>
    <meta charset="utf-8">
    <title>SEND-C</title>
    <style>
      body { font-family: Arial, sans-serif; margin: 0; background: #f3f4f6; color: #111827; }
      .page { max-width: 480px; margin: 60px auto; padding: 24px; background: white; border-radius: 16px; box-shadow: 0 10px 30px rgba(0,0,0,0.08); }
      h1 { margin-top: 0; }
      form { display: flex; flex-direction: column; gap: 12px; }
      input, button { padding: 10px; font-size: 16px; }
      .msg { color: #b91c1c; margin-top: 8px; }
      .link { margin-top: 12px; }
    </style>
  </head>
  <body>
    <div class="page">
      <h1>SEND-C</h1>
      {% if session.get('user') %}
        <p>Welcome, {{ session['user'] }}.</p>
        <p><a href="/logout">Logout</a></p>
      {% else %}
        <form method="post" action="/login">
          <input name="username" placeholder="Username" required>
          <input name="password" type="password" placeholder="Password" required>
          <button type="submit">Login</button>
        </form>
        {% if message %}<div class="msg">{{ message }}</div>{% endif %}
        <div class="link"><a href="/register">Create account</a></div>
      {% endif %}
    </div>
  </body>
</html>
"""

REGISTER_TEMPLATE = """
<!doctype html>
<html>
  <head>
    <meta charset="utf-8">
    <title>Create account</title>
    <style>
      body { font-family: Arial, sans-serif; margin: 0; background: #f3f4f6; }
      .page { max-width: 480px; margin: 60px auto; padding: 24px; background: white; border-radius: 16px; }
      form { display: flex; flex-direction: column; gap: 12px; }
      input, button { padding: 10px; font-size: 16px; }
      .msg { color: #b91c1c; margin-top: 8px; }
    </style>
  </head>
  <body>
    <div class="page">
      <h1>Create account</h1>
      <form method="post" action="/register">
        <input name="username" placeholder="Username" required>
        <input name="password" type="password" placeholder="Password" required>
        <button type="submit">Create account</button>
      </form>
      {% if message %}<div class="msg">{{ message }}</div>{% endif %}
      <p><a href="/">Back to login</a></p>
    </div>
  </body>
</html>
"""


@app.route("/")
def index():
    return render_template_string(HTML_TEMPLATE, message=None)


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = (request.form.get("username") or "").strip()
        password = (request.form.get("password") or "").strip()
        if backend.verify_user_login(username, password):
            session["user"] = username
            return redirect(url_for("dashboard"))
        return render_template_string(HTML_TEMPLATE, message="Invalid username or password")
    return redirect(url_for("index"))


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = (request.form.get("username") or "").strip()
        password = (request.form.get("password") or "").strip()
        if not username or not password:
            return render_template_string(REGISTER_TEMPLATE, message="Username and password are required")
        backend.register_user(username, password)
        session["user"] = username
        return redirect(url_for("dashboard"))
    return render_template_string(REGISTER_TEMPLATE, message=None)


@app.route("/dashboard")
def dashboard():
    if not session.get("user"):
        return redirect(url_for("index"))
    students = backend.get_all_students_list()
    return render_template_string("""
    <!doctype html>
    <html>
      <head><meta charset="utf-8"><title>Dashboard</title></head>
      <body style="font-family: Arial, sans-serif; margin: 24px;">
        <h1>Dashboard</h1>
        <p>Welcome, {{ user }}.</p>
        <p><a href="/logout">Logout</a></p>
        <h2>Students</h2>
        <ul>
          {% for student in students %}
            <li>{{ student.get('full_name') or student.get('student_id') or 'Unnamed student' }}</li>
          {% endfor %}
        </ul>
      </body>
    </html>
    """, user=session["user"], students=students)


@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
