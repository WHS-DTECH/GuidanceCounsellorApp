import os
import time
from flask import Flask, request, redirect, session, url_for, render_template_string

from database import StudentBackend
from dashboard import DASHBOARD_WEB_TEMPLATE, build_dashboard_context
from login import render_login_page, render_register_page
from search import filter_students, render_search_page
from editor import build_empty_student, normalize_student_payload, render_editor_page
from google_auth import build_google_auth_url, exchange_code_for_token, fetch_google_user_info
from navbar import build_global_navbar


app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "dev-secret-key")
app.config["PREFERRED_URL_SCHEME"] = "https"

backend = StudentBackend()
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")
GOOGLE_REDIRECT_URI = os.getenv(
    "GOOGLE_REDIRECT_URI",
    "https://guidancecounsellorapp.onrender.com/auth/google/callback",
)


def current_user():
    return session.get("user")


def current_role():
    user = current_user()
    if not user:
        return None
    role = backend.get_user_role(user)
    session["role"] = role
    if role not in {"ADMIN", "Counsellor", "AppBuilder"}:
        return "Counsellor"
    return role


def login_required():
    return current_user() is not None


def current_global_navbar():
    role = current_role()
    return build_global_navbar(role)


def students_for_role(role):
    if role == "AppBuilder":
        return backend.get_dummy_students(), "dummy dataset", False
    return backend.get_all_students_list(), "live dataset", True


def find_student_by_id(student_id):
    for student in backend.get_all_students_list():
        if student.get("student_id") == student_id:
            return student
    return None


@app.route("/")
def index():
    if current_user():
        return render_login_page(
            user=current_user(),
            role=current_role(),
            google_enabled=bool(GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET),
            global_navbar=current_global_navbar(),
        )
    return render_login_page(google_enabled=bool(GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET))


@app.route("/login", methods=["POST"])
def login():
    username = (request.form.get("username") or "").strip()
    password = (request.form.get("password") or "").strip()
    if backend.verify_user_login(username, password):
        session["user"] = username
        session["role"] = backend.get_user_role(username)
        return redirect(url_for("dashboard"))
    return render_login_page(
        message="Invalid username or password",
        google_enabled=bool(GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET),
    )


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = (request.form.get("username") or "").strip()
        password = (request.form.get("password") or "").strip()
        if not username or not password:
            return render_register_page(message="Username and password are required")
        backend.register_user(username, password)
        if backend.get_user_role(username) not in {"ADMIN", "Counsellor", "AppBuilder"}:
            backend.set_user_role(username, "Counsellor")
        session["user"] = username
        session["role"] = backend.get_user_role(username)
        return redirect(url_for("dashboard"))
    return render_register_page()


@app.route("/auth/google/login")
def google_login():
    if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
        return redirect(url_for("index"))
    return redirect(build_google_auth_url(GOOGLE_CLIENT_ID, GOOGLE_REDIRECT_URI))


@app.route("/auth/google/callback")
def google_callback():
    code = (request.args.get("code") or "").strip()
    if not code:
        return render_login_page(
            message="Google login was cancelled.",
            google_enabled=bool(GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET),
        )

    access_token = exchange_code_for_token(
        code,
        GOOGLE_CLIENT_ID,
        GOOGLE_CLIENT_SECRET,
        GOOGLE_REDIRECT_URI,
    )
    if not access_token:
        return render_login_page(
            message="Google login failed.",
            google_enabled=bool(GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET),
        )

    user_info = fetch_google_user_info(access_token)
    email = (user_info.get("email") or "").strip()
    if not email:
        return render_login_page(
            message="Google login did not return an email address.",
            google_enabled=bool(GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET),
        )

    backend.set_google_login(email, user_info.get("name") or email)
    if backend.get_user_role(email) not in {"ADMIN", "Counsellor", "AppBuilder"}:
        backend.set_user_role(email, "Counsellor")

    session["user"] = email
    session["role"] = backend.get_user_role(email)
    return redirect(url_for("dashboard"))


@app.route("/dashboard")
def dashboard():
    if not login_required():
        return redirect(url_for("index"))

    role = current_role()
    students, data_label, _ = students_for_role(role)
    context = build_dashboard_context(
        user=current_user(),
        role=role,
        data_label=data_label,
        students=students,
    )
    context["global_navbar"] = current_global_navbar()
    return render_template_string(DASHBOARD_WEB_TEMPLATE, **context)


@app.route("/students")
def students():
    if not login_required():
        return redirect(url_for("index"))

    role = current_role()
    all_students, data_label, can_edit = students_for_role(role)
    query = (request.args.get("q") or "").strip()
    filtered = filter_students(all_students, query)
    return render_search_page(
        students=filtered,
        query=query,
        role=role,
        data_label=data_label,
        is_admin=(role == "ADMIN"),
        can_edit=can_edit,
        message=None if can_edit else "AppBuilder can view students using dummy data only.",
        global_navbar=current_global_navbar(),
    )


@app.route("/students/edit", methods=["GET", "POST"])
def students_edit():
    if not login_required():
        return redirect(url_for("index"))

    role = current_role()
    if role == "AppBuilder":
        return render_search_page(
            students=filter_students(backend.get_dummy_students(), ""),
            query="",
            role=role,
            data_label="dummy dataset",
            is_admin=False,
            can_edit=False,
            message="AppBuilder does not have write access to live student data.",
            global_navbar=current_global_navbar(),
        )

    if request.method == "POST":
        requested_id = (request.form.get("student_id") or "").strip()
        existing = find_student_by_id(requested_id) if requested_id else None
        student_id = requested_id or f"ST-{int(time.time())}"
        payload = normalize_student_payload(request.form, existing_student_id=student_id)
        payload["student_id"] = student_id
        backend.upsert_student(student_id, payload)
        return redirect(url_for("students"))

    requested_id = (request.args.get("student_id") or "").strip()
    if requested_id:
        student = find_student_by_id(requested_id)
        if not student:
            return render_editor_page(
                build_empty_student(requested_id),
                message="Student not found. You can save to create a new record.",
                global_navbar=current_global_navbar(),
            )
        return render_editor_page(student, global_navbar=current_global_navbar())

    return render_editor_page(
        build_empty_student(f"ST-{int(time.time())}"),
        global_navbar=current_global_navbar(),
    )


@app.route("/students/delete", methods=["POST"])
def students_delete():
    if not login_required():
        return redirect(url_for("index"))

    role = current_role()
    if role == "AppBuilder":
        return redirect(url_for("students"))

    student_id = (request.form.get("student_id") or "").strip()
    if student_id:
        backend.delete_student(student_id)
    return redirect(url_for("students"))


@app.route("/infrastructure")
def infrastructure():
    if not login_required():
        return redirect(url_for("index"))

    role = current_role()
    if role not in {"ADMIN", "Counsellor", "AppBuilder"}:
        return redirect(url_for("dashboard"))

    students, data_label, _ = students_for_role(role)
    return render_template_string(
        """
        <!doctype html>
        <html>
          <head><meta charset="utf-8"><title>Infrastructure</title></head>
          <body style="font-family: Arial, sans-serif; margin: 24px;">
                        {{ global_navbar|safe }}
            <h1>Infrastructure</h1>
            <p>Role: {{ role }}</p>
            <p>This view is restricted to {{ data_label }} for AppBuilder users.</p>
            <p><a href="/dashboard">Dashboard</a> | <a href="/students">Students</a> | <a href="/logout">Logout</a></p>
            <h2>Sample infrastructure records</h2>
            <ul>
              {% for student in students %}
                <li>{{ student.get('student_id') }} - {{ student.get('full_name') }}</li>
              {% endfor %}
            </ul>
          </body>
        </html>
        """,
        role=role,
        data_label=data_label,
        students=students,
        global_navbar=current_global_navbar(),
    )


@app.route("/user-roles", methods=["GET", "POST"])
def user_roles():
    if not login_required():
        return redirect(url_for("index"))

    role = current_role()
    if role != "ADMIN":
        return render_template_string(
            """
            <!doctype html>
            <html>
              <body>
                                {{ global_navbar|safe }}
                <h1>Access denied</h1>
                <p>This page is restricted to administrators.</p>
                <p><a href="/dashboard">Back to dashboard</a></p>
              </body>
            </html>
                        """,
                        global_navbar=current_global_navbar(),
        )

    message = None
    if request.method == "POST":
        username = (request.form.get("username") or "").strip()
        selected_role = (request.form.get("role") or "Counsellor").strip()
        if username:
            backend.set_user_role(username, selected_role)
            session["role"] = backend.get_user_role(current_user())
            message = f"Updated role for {username}."

    users = backend.list_user_roles()
    return render_template_string(
        """
        <!doctype html>
        <html>
          <head><meta charset="utf-8"><title>User Roles</title></head>
          <body style="font-family: Arial, sans-serif; margin: 24px;">
                        {{ global_navbar|safe }}
            <h1>User Role Management</h1>
            <p><a href="/dashboard">Dashboard</a> | <a href="/students">Students</a> | <a href="/logout">Logout</a></p>
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
        """,
        message=message,
        users=users,
        global_navbar=current_global_navbar(),
    )


@app.route("/logout")
def logout():
    session.pop("user", None)
    session.pop("role", None)
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
