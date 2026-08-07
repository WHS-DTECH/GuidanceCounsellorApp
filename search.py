from flask import render_template_string


SEARCH_TEMPLATE = """
<!doctype html>
<html>
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Students</title>
    <style>
      body { font-family: Arial, sans-serif; margin: 0; background: #f3f4f6; color: #111827; }
      .wrap { max-width: 1100px; margin: 24px auto; padding: 0 16px 24px; }
      .card { background: white; border-radius: 14px; padding: 16px; box-shadow: 0 8px 20px rgba(0,0,0,0.06); }
      .top { display: flex; justify-content: space-between; align-items: center; gap: 10px; flex-wrap: wrap; }
      .controls { display: flex; gap: 8px; flex-wrap: wrap; margin-top: 10px; }
      input, button, select { padding: 8px 10px; font-size: 14px; }
      table { width: 100%; border-collapse: collapse; margin-top: 12px; }
      th, td { border-bottom: 1px solid #e5e7eb; padding: 10px; text-align: left; }
      .muted { color: #6b7280; }
      .danger { color: #b91c1c; }
      .row-actions a, .row-actions button { margin-right: 8px; }
      form.inline { display: inline; }
    </style>
  </head>
  <body>
    <div class="wrap">
      <div class="card">
        <div class="top">
          <h1>Student Database</h1>
          <div>
            <a href="/dashboard">Dashboard</a>
            {% if is_admin %}| <a href="/user-roles">User Roles</a>{% endif %}
            | <a href="/logout">Logout</a>
          </div>
        </div>

        <p class="muted">Role: {{ role }} | Data source: {{ data_label }}</p>

        {% if message %}<p class="danger">{{ message }}</p>{% endif %}

        <form method="get" action="/students" class="controls">
          <input type="text" name="q" placeholder="Search by name or ID" value="{{ query }}">
          <button type="submit">Search</button>
          {% if can_edit %}<a href="/students/edit">Add Student</a>{% endif %}
        </form>

        <table>
          <thead>
            <tr>
              <th>ID</th>
              <th>Name</th>
              <th>Preferred</th>
              <th>Gender</th>
              <th>Ethnicity</th>
              <th>Referral</th>
              <th>Sessions</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {% for s in students %}
            <tr>
              <td>{{ s.get('student_id', '') }}</td>
              <td>{{ s.get('full_name', '') }}</td>
              <td>{{ s.get('preferred_name', '') }}</td>
              <td>{{ s.get('gender', '') }}</td>
              <td>{{ s.get('ethnicity', '') }}</td>
              <td>{{ s.get('referral_type', '') }}</td>
              <td>{{ s.get('sessions', [])|length }}</td>
              <td class="row-actions">
                <a href="/students/edit?student_id={{ s.get('student_id', '') }}">Edit</a>
                {% if can_edit %}
                <form method="post" action="/students/delete" class="inline" onsubmit="return confirm('Delete this student?');">
                  <input type="hidden" name="student_id" value="{{ s.get('student_id', '') }}">
                  <button type="submit">Delete</button>
                </form>
                {% endif %}
              </td>
            </tr>
            {% endfor %}
          </tbody>
        </table>
      </div>
    </div>
  </body>
</html>
"""


def filter_students(students, query):
    q = (query or "").strip().lower()
    if not q:
        return students
    filtered = []
    for student in students:
        student_id = str(student.get("student_id", "")).lower()
        full_name = str(student.get("full_name", "")).lower()
        if q in student_id or q in full_name:
            filtered.append(student)
    return filtered


def render_search_page(students, query, role, data_label, is_admin=False, can_edit=True, message=None):
    return render_template_string(
        SEARCH_TEMPLATE,
        students=students,
        query=query,
        role=role,
        data_label=data_label,
        is_admin=is_admin,
        can_edit=can_edit,
        message=message,
    )
