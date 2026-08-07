import datetime
from flask import render_template_string


EDITOR_TEMPLATE = """
<!doctype html>
<html>
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>{{ page_title }}</title>
    <style>
      body { font-family: Arial, sans-serif; margin: 0; background: #f3f4f6; color: #111827; }
      .wrap { max-width: 1100px; margin: 24px auto; padding: 0 16px 24px; }
      .card { background: white; border-radius: 14px; padding: 16px; box-shadow: 0 8px 20px rgba(0,0,0,0.06); }
      .grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 12px; }
      .full { grid-column: 1 / -1; }
      label { display: block; font-size: 13px; color: #6b7280; margin-bottom: 4px; }
      input, textarea, select, button { width: 100%; padding: 10px; font-size: 14px; }
      textarea { min-height: 100px; }
      .actions { display: flex; gap: 8px; margin-top: 12px; }
      .actions a, .actions button { width: auto; }
      .msg { color: #b91c1c; }
      @media (max-width: 900px) { .grid { grid-template-columns: 1fr; } }
    </style>
  </head>
  <body>
    <div class="wrap">
      <div class="card">
        <h1>{{ page_title }}</h1>
        <p><a href="/students">Back to Students</a> | <a href="/dashboard">Dashboard</a> | <a href="/logout">Logout</a></p>
        {% if message %}<p class="msg">{{ message }}</p>{% endif %}
        <form method="post" action="/students/edit">
          <input type="hidden" name="student_id" value="{{ student.get('student_id', '') }}">
          <div class="grid">
            <div>
              <label>Full Name</label>
              <input name="full_name" value="{{ student.get('full_name', '') }}" required>
            </div>
            <div>
              <label>Preferred Name</label>
              <input name="preferred_name" value="{{ student.get('preferred_name', '') }}">
            </div>
            <div>
              <label>Date of Birth (DD.MM.YYYY)</label>
              <input name="dob" value="{{ student.get('dob', '') }}">
            </div>
            <div>
              <label>Age (calculated)</label>
              <input value="{{ age }}" disabled>
            </div>
            <div>
              <label>Gender</label>
              <input name="gender" value="{{ student.get('gender', '') }}">
            </div>
            <div>
              <label>Ethnicity</label>
              <input name="ethnicity" value="{{ student.get('ethnicity', '') }}">
            </div>
            <div>
              <label>Address</label>
              <input name="address" value="{{ student.get('address', '') }}">
            </div>
            <div>
              <label>Phone</label>
              <input name="phone" value="{{ student.get('phone', '') }}">
            </div>
            <div>
              <label>Whānau</label>
              <input name="whanau" value="{{ student.get('whanau', '') }}">
            </div>
            <div>
              <label>Care Giver</label>
              <input name="care_giver" value="{{ student.get('care_giver', '') }}">
            </div>
            <div class="full">
              <label>Referral Type</label>
              <input name="referral_type" value="{{ student.get('referral_type', '') }}">
            </div>
            <div class="full">
              <label>Session Times (comma-separated, HH:MM DD.MM.YYYY)</label>
              <input name="sessions_list" value="{{ sessions_string }}">
            </div>
            <div class="full">
              <label>Notes</label>
              <textarea name="notes">{{ student.get('notes', '') }}</textarea>
            </div>
          </div>
          <div class="actions">
            <button type="submit">Save Student Profile</button>
          </div>
        </form>
      </div>
    </div>
  </body>
</html>
"""


def build_empty_student(student_id):
    return {
        "student_id": student_id,
        "full_name": "",
        "preferred_name": "",
        "dob": "",
        "gender": "",
        "ethnicity": "",
        "address": "",
        "phone": "",
        "referral_type": "",
        "whanau": "",
        "care_giver": "",
        "notes": "",
        "sessions": [],
    }


def calculate_age(dob_str):
    raw = (dob_str or "").strip()
    if not raw:
        return "-"
    try:
        birth_date = datetime.datetime.strptime(raw, "%d.%m.%Y")
        today = datetime.datetime.now()
        age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
        return str(age) if age >= 0 else "-"
    except ValueError:
        return "-"


def parse_to_iso_session(formatted_str):
    raw = (formatted_str or "").strip()
    if not raw:
        return ""
    try:
        parsed_dt = datetime.datetime.strptime(raw, "%H:%M %d.%m.%Y")
        return parsed_dt.strftime("%Y-%m-%d %H:%M")
    except ValueError:
        return raw


def format_session_time(iso_or_raw_str):
    raw = (iso_or_raw_str or "").strip()
    if not raw:
        return ""
    try:
        parsed_dt = datetime.datetime.fromisoformat(raw[:16].replace(" ", "T"))
        return parsed_dt.strftime("%H:%M %d.%m.%Y")
    except ValueError:
        return raw


def normalize_student_payload(form_data, existing_student_id=""):
    student_id = (form_data.get("student_id") or "").strip() or existing_student_id
    sessions_raw = (form_data.get("sessions_list") or "").strip()
    sessions = []
    if sessions_raw:
        for chunk in sessions_raw.split(","):
            parsed = parse_to_iso_session(chunk.strip())
            if parsed:
                sessions.append(parsed)

    return {
        "student_id": student_id,
        "full_name": (form_data.get("full_name") or "").strip(),
        "preferred_name": (form_data.get("preferred_name") or "").strip(),
        "dob": (form_data.get("dob") or "").strip(),
        "gender": (form_data.get("gender") or "").strip(),
        "ethnicity": (form_data.get("ethnicity") or "").strip(),
        "address": (form_data.get("address") or "").strip(),
        "phone": (form_data.get("phone") or "").strip(),
        "referral_type": (form_data.get("referral_type") or "").strip(),
        "whanau": (form_data.get("whanau") or "").strip(),
        "care_giver": (form_data.get("care_giver") or "").strip(),
        "notes": (form_data.get("notes") or "").strip(),
        "sessions": sessions,
    }


def render_editor_page(student, message=None):
    sessions_string = ", ".join(format_session_time(s) for s in student.get("sessions", []))
    page_title = "Edit Student Profile" if student.get("student_id") else "New Student Profile"
    return render_template_string(
        EDITOR_TEMPLATE,
        student=student,
        message=message,
        sessions_string=sessions_string,
        age=calculate_age(student.get("dob", "")),
        page_title=page_title,
    )
