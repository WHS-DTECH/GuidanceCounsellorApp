import os
import json
import urllib.parse
import urllib.request
from flask import Flask, render_template_string, request, redirect, session, url_for
from database import StudentBackend
from dashboard import DASHBOARD_WEB_TEMPLATE, build_dashboard_context

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "dev-secret-key")
app.config["PREFERRED_URL_SCHEME"] = "https"

backend = StudentBackend()
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")
GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI", "https://guidancecounsellorapp.onrender.com/auth/google/callback")

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
      .admin-btn { display: inline-block; margin-top: 10px; padding: 8px 12px; border-radius: 8px; background: #1f2937; color: white; text-decoration: none; }
    </style>
  </head>
  <body>
    <div class="page">
      <h1>SEND-C</h1>
      {% if session.get('user') %}
        <p>Welcome, {{ session['user'] }}.</p>
        <p>Role: {{ role }}</p>
        <p><a href="/dashboard">Dashboard</a></p>
        {% if role == 'ADMIN' %}<p><a class="admin-btn" href="/user-roles">Admin Items</a></p>{% endif %}
        <p><a href="/logout">Logout</a></p>
      {% else %}
        <form method="post" action="/login">
          <input name="username" placeholder="Username" required>
          <input name="password" type="password" placeholder="Password" required>
          <button type="submit">Login</button>
        </form>
        {% if message %}<div class="msg">{{ message }}</div>{% endif %}
        {% if google_enabled %}
          <div class="link"><a href="/auth/google/login">Sign in with Google</a></div>
        {% endif %}
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


def current_role():
    if session.get("user"):
        return session.get("role") or backend.get_user_role(session["user"])
    return None


@app.route("/")
def index():
    if session.get("user"):
        return redirect(url_for("dashboard"))
    return render_template_string(HTML_TEMPLATE, message=None, role=None, google_enabled=bool(GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = (request.form.get("username") or "").strip()
        password = (request.form.get("password") or "").strip()
        if backend.verify_user_login(username, password):
            session["user"] = username
            session["role"] = backend.get_user_role(username)
            return redirect(url_for("dashboard"))
        return render_template_string(HTML_TEMPLATE, message="Invalid username or password", role=None, google_enabled=bool(GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET))
    return redirect(url_for("index"))


@app.route("/auth/google/login")
def google_login():
    if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
        return redirect(url_for("index"))

    params = {
        "client_id": GOOGLE_CLIENT_ID,
        "redirect_uri": GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope": "openid email profile",
        "access_type": "offline",
        "prompt": "consent",
    }
    auth_url = "https://accounts.google.com/o/oauth2/v2/auth?" + urllib.parse.urlencode(params)
    return redirect(auth_url)


@app.route("/auth/google/callback")
def google_callback():
    code = request.args.get("code", "")
    if not code:
        return render_template_string(HTML_TEMPLATE, message="Google login was cancelled.", role=None, google_enabled=bool(GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET))

    data = urllib.parse.urlencode({
        "code": code,
        "client_id": GOOGLE_CLIENT_ID,
        "client_secret": GOOGLE_CLIENT_SECRET,
        "redirect_uri": GOOGLE_REDIRECT_URI,
        "grant_type": "authorization_code",
    }).encode("utf-8")

    request_obj = urllib.request.Request(
        "https://oauth2.googleapis.com/token",
        data=data,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )

    with urllib.request.urlopen(request_obj) as response:
        token_data = json.load(response)

    access_token = token_data.get("access_token")
    if not access_token:
        return render_template_string(HTML_TEMPLATE, message="Google login failed.", role=None, google_enabled=bool(GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET))

    user_info_request = urllib.request.Request(
        "https://www.googleapis.com/oauth2/v2/userinfo",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    with urllib.request.urlopen(user_info_request) as response:
        user_info = json.load(response)

    email = (user_info.get("email") or "").strip()
    if not email:
        return render_template_string(HTML_TEMPLATE, message="Google login did not return an email address.", role=None, google_enabled=bool(GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET))

    if not backend.get_stored_user() or not backend.verify_user_login(email, "google-oauth"):
        backend.register_user(email, "google-oauth")
        backend.set_user_role(email, "Counsellor")
    backend.set_google_login(email, user_info.get("name") or email)

    session["user"] = email
    session["role"] = backend.get_user_role(email)
    return redirect(url_for("dashboard"))


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = (request.form.get("username") or "").strip()
        password = (request.form.get("password") or "").strip()
        if not username or not password:
            return render_template_string(REGISTER_TEMPLATE, message="Username and password are required")
        initial_role = "ADMIN" if not backend.has_registered_user() else "Counsellor"
        backend.register_user(username, password)
        backend.set_user_role(username, initial_role)
        session["user"] = username
        session["role"] = backend.get_user_role(username)
        return redirect(url_for("dashboard"))
    return render_template_string(REGISTER_TEMPLATE, message=None)


@app.route("/dashboard")
def dashboard():
    if not session.get("user"):
        return redirect(url_for("index"))

    role = session.get("role") or backend.get_user_role(session["user"])
    if role not in {"ADMIN", "Counsellor", "AppBuilder"}:
        role = "Counsellor"

    students = backend.get_dummy_students() if role == "AppBuilder" else backend.get_all_students_list()
    data_label = "dummy dataset" if role == "AppBuilder" else "live dataset"
    context = build_dashboard_context(
        user=session["user"],
        role=role,
        data_label=data_label,
        students=students,
    )
    return render_template_string(DASHBOARD_WEB_TEMPLATE, **context)


@app.route("/infrastructure")
def infrastructure():
    if not session.get("user"):
        return redirect(url_for("index"))

    role = session.get("role") or backend.get_user_role(session["user"])
    if role not in {"ADMIN", "Counsellor", "AppBuilder"}:
        return redirect(url_for("dashboard"))

    students = backend.get_dummy_students() if role == "AppBuilder" else backend.get_all_students_list()
    return render_template_string("""
    <!doctype html>
    <html>
      <head><meta charset="utf-8"><title>Infrastructure</title></head>
      <body style="font-family: Arial, sans-serif; margin: 24px;">
        <h1>Infrastructure</h1>
        <p>Role: {{ role }}</p>
        <p>This view is restricted to {{ data_label }} for AppBuilder users.</p>
        <p><a href="/dashboard">Dashboard</a> | <a href="/logout">Logout</a></p>
        <h2>Sample infrastructure records</h2>
        <ul>
          {% for student in students %}
            <li>{{ student.get('student_id') }} - {{ student.get('full_name') }}</li>
          {% endfor %}
        </ul>
      </body>
    </html>
    """, role=role, data_label="dummy dataset" if role == "AppBuilder" else "live dataset", students=students)


@app.route("/user-roles", methods=["GET", "POST"])
def user_roles():
    if not session.get("user"):
        return redirect(url_for("index"))

    role = session.get("role") or backend.get_user_role(session["user"])
    if role != "ADMIN":
        return render_template_string("""
        <!doctype html>
        <html><body><h1>Access denied</h1><p>This page is restricted to administrators.</p><p><a href="/dashboard">Back to dashboard</a></p></body></html>
        """)

    message = None
    if request.method == "POST":
        username = (request.form.get("username") or "").strip()
        selected_role = (request.form.get("role") or "Counsellor").strip()
        if username:
            backend.set_user_role(username, selected_role)
            session["role"] = backend.get_user_role(session["user"])
            message = f"Updated role for {username}."

    users = backend.list_user_roles()
    return render_template_string("""
    <!doctype html>
    <html>
      <head><meta charset="utf-8"><title>User Roles</title></head>
      <body style="font-family: Arial, sans-serif; margin: 24px;">
        <h1>User Role Management</h1>
        <p><a href="/dashboard">Dashboard</a> | <a href="/logout">Logout</a></p>
        {% if message %}<p><strong>{{ message }}</strong></p>{% endif %}
        <form method="post" style="display:flex; flex-direction:column; gap:10px; max-width:360px;">
          <label>Username</label>
          <select name="username">
            {% for user in users %}
              <option value="{{ user.username }}">{{ user.username }}</option>
            {% endfor %}
          </select>
          <label>Role</label>
          <select name="role">
            <option value="ADMIN">ADMIN</option>
            <option value="Counsellor">Counsellor</option>
            <option value="AppBuilder">AppBuilder</option>
          </select>
          <button type="submit">Save role</button>
        </form>
        <h2>Current assignments</h2>
        <ul>
          {% for user in users %}
            <li>{{ user.username }} - {{ user.role }}</li>
          {% endfor %}
        </ul>
      </body>
    </html>
    """, message=message, users=users)


@app.route("/logout")
def logout():
    session.pop("user", None)
    session.pop("role", None)
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
