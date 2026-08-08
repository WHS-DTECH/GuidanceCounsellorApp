from flask import render_template_string


LOGIN_TEMPLATE = """
<!doctype html>
<html>
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>SEND-C Login</title>
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
    {{ global_navbar|safe }}
    <div class="page">
      <h1>SEND-C</h1>
      {% if user %}
        <p>Welcome, {{ user }}.</p>
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
    {{ global_footer|safe }}
  </body>
</html>
"""


REGISTER_TEMPLATE = """
<!doctype html>
<html>
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
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
    {{ global_navbar|safe }}
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
    {{ global_footer|safe }}
  </body>
</html>
"""


def render_login_page(message=None, user=None, role=None, google_enabled=False, global_navbar=""):
    return render_template_string(
        LOGIN_TEMPLATE,
        message=message,
        user=user,
        role=role,
        google_enabled=google_enabled,
    global_navbar=global_navbar,
    )


def render_register_page(message=None, global_navbar=""):
  return render_template_string(REGISTER_TEMPLATE, message=message, global_navbar=global_navbar)
