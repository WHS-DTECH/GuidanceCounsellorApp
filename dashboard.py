from collections import Counter
import datetime


DASHBOARD_WEB_TEMPLATE = """
<!doctype html>
<html>
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Dashboard</title>
    <style>
      :root {
        --bg: #eef1f7;
        --card: #ffffff;
        --text: #1a243b;
        --muted: #8a93a3;
        --blue: #3a78e8;
        --green: #23c06a;
        --nav-bg: #232f45;
        --nav-pill: #3a465d;
      }
      * { box-sizing: border-box; }
      body {
        margin: 0;
        font-family: Arial, sans-serif;
        background: var(--bg);
        color: var(--text);
      }

      .app-shell {
        display: grid;
        grid-template-columns: 300px 1fr;
        min-height: calc(100vh - 52px);
      }

      .sidebar {
        background: var(--nav-bg);
        color: #ffffff;
        padding: 26px 20px;
        display: flex;
        flex-direction: column;
      }
      .brand {
        font-size: 44px;
        font-weight: 800;
        letter-spacing: 1px;
        margin: 6px 0 26px;
      }
      .nav-link {
        display: inline-block;
        padding: 14px 16px;
        border-radius: 12px;
        color: #ffffff;
        text-decoration: none;
        font-weight: 700;
      }
      .nav-link.active { background: var(--nav-pill); }
      .nav-link.secondary { margin-top: 8px; opacity: 0.82; }
      .sidebar-footer { margin-top: auto; }
      .session-btn {
        display: inline-block;
        background: var(--green);
        color: white;
        font-weight: 700;
        text-decoration: none;
        padding: 10px 16px;
        border-radius: 999px;
      }

      .main {
        padding: 28px 34px;
      }
      .title { margin: 0; font-size: 50px; letter-spacing: 0.2px; }
      .meta { color: var(--muted); margin: 6px 0; font-size: 18px; }
      .logout-line { margin-top: 12px; }
      .logout-line a { color: #334155; }

      .stats {
        margin-top: 22px;
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 18px;
      }
      .card {
        background: var(--card);
        border-radius: 18px;
        padding: 22px;
        box-shadow: 0 10px 20px rgba(15, 23, 42, 0.05);
      }
      .stat-label { color: #a1a6b0; font-size: 18px; }
      .stat-value { font-size: 44px; font-weight: 800; margin-top: 6px; }

      .charts {
        margin-top: 20px;
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 18px;
      }
      .chart-card h3 { margin-top: 0; margin-bottom: 14px; font-size: 36px; }
      .chart-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 12px;
      }

      .dropdown-pill {
        padding: 8px 12px;
        border-radius: 10px;
        border: 1px solid #dbe3ef;
        background: #f8fafc;
        color: #3a78e8;
        font-weight: 700;
      }

      .distribution-list { margin-top: 6px; }
      .distribution-row { margin-bottom: 24px; }
      .distribution-top {
        display: flex;
        justify-content: space-between;
        align-items: baseline;
        margin-bottom: 8px;
      }
      .distribution-name { font-size: 22px; }
      .distribution-meta { color: #9ca3af; font-size: 14px; }
      .distribution-track {
        width: 100%;
        height: 14px;
        background: #dbe3ef;
        border-radius: 999px;
      }
      .distribution-fill {
        height: 100%;
        background: var(--blue);
        border-radius: 999px;
      }

      .timeline-toolbar {
        display: flex;
        gap: 8px;
        flex-wrap: wrap;
        margin-bottom: 14px;
      }
      .export-btn {
        display: inline-block;
        background: var(--blue);
        color: #fff;
        text-decoration: none;
        font-weight: 700;
        padding: 10px 14px;
        border-radius: 999px;
      }
      .timeline-area {
        margin-top: 18px;
        min-height: 270px;
        border-top: 1px solid #dde3ec;
        display: grid;
        grid-template-columns: repeat(12, minmax(0, 1fr));
        gap: 12px;
        align-items: end;
        padding-top: 18px;
      }
      .timeline-col {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: end;
      }
      .timeline-bar {
        width: 28px;
        border-radius: 8px;
        background: var(--green);
      }
      .timeline-label {
        margin-top: 8px;
        color: #8090a7;
        font-size: 12px;
        font-weight: 700;
      }

      @media (max-width: 980px) {
        .app-shell { grid-template-columns: 1fr; }
        .sidebar { display: none; }
        .stats { grid-template-columns: 1fr; }
        .charts { grid-template-columns: 1fr; }
      }

      @media (max-width: 700px) {
        .main { padding: 18px 14px; }
        .title { font-size: 34px; }
        .chart-card h3 { font-size: 28px; }
        .stat-value { font-size: 34px; }
        .distribution-name { font-size: 18px; }
        .timeline-bar { width: 18px; }
      }
    </style>
  </head>
  <body>
    {{ global_navbar|safe }}
    <div class="app-shell">
      <aside class="sidebar">
        <div class="brand">SEND-C</div>
        <a class="nav-link active" href="/dashboard">DASHBOARD</a>
        <a class="nav-link secondary" href="/students">STUDENTS</a>
        <div class="sidebar-footer">
          <a class="session-btn" href="/students/edit">NEW SESSION</a>
        </div>
      </aside>

      <main class="main">
        <h1 class="title">Overview & Analytics</h1>
        <p class="meta">Welcome, {{ user }}.</p>
        <p class="meta">Role: {{ role }} | Viewing {{ data_label }}.</p>
        <p class="logout-line"><a href="/logout">Logout</a></p>

        <div class="stats">
          <div class="card">
            <div class="stat-label">Total Registered Students</div>
            <div class="stat-value" style="color: var(--blue);">{{ total_students }}</div>
          </div>
          <div class="card">
            <div class="stat-label">Total Sessions Logged</div>
            <div class="stat-value" style="color: var(--green);">{{ total_sessions }}</div>
          </div>
        </div>

        <div class="charts">
          <div class="card chart-card">
            <div class="chart-header">
              <h3>Distribution Profiles</h3>
              <span class="dropdown-pill">Gender</span>
            </div>

            <div class="distribution-list">
              {% if distribution_rows %}
                {% for row in distribution_rows %}
                  <div class="distribution-row">
                    <div class="distribution-top">
                      <div class="distribution-name">{{ row.label }}</div>
                      <div class="distribution-meta">{{ row.count }}x ({{ row.percent }}%)</div>
                    </div>
                    <div class="distribution-track">
                      <div class="distribution-fill" style="width: {{ row.percent }}%;"></div>
                    </div>
                  </div>
                {% endfor %}
              {% else %}
                <p class="meta">No gender data available.</p>
              {% endif %}
            </div>
          </div>

          <div class="card chart-card">
            <h3>Session Tracking Timeline</h3>
            <div class="timeline-toolbar">
              <span class="dropdown-pill">Total Sessions</span>
              <span class="dropdown-pill">Full Year</span>
              <a class="export-btn" href="/students">Export (.csv)</a>
            </div>

            <div class="timeline-area">
              {% for item in timeline_bars %}
                <div class="timeline-col" title="{{ item.value }} sessions">
                  <div class="timeline-bar" style="height: {{ item.height }}px;"></div>
                  <div class="timeline-label">{{ item.label }}</div>
                </div>
              {% endfor %}
            </div>
          </div>
        </div>
      </main>
    </div>
  </body>
</html>
"""


def _normalize_value(value):
    text = str(value or "").strip()
    return text if text else "Unspecified"


def _distribution(students, key_name):
    counts = Counter(_normalize_value(student.get(key_name)) for student in students)
    labels = list(counts.keys())
    values = [counts[label] for label in labels]
    return {"labels": labels, "values": values}


def _timeline_last_12_months(students):
    now = datetime.datetime.now()
    month_keys = []
    for i in range(11, -1, -1):
        d = now.replace(day=1) - datetime.timedelta(days=i * 30)
        month_keys.append(d.strftime("%Y-%m"))

    counts = {k: 0 for k in month_keys}
    for student in students:
        for session_stamp in student.get("sessions", []):
            month_key = str(session_stamp or "")[:7]
            if month_key in counts:
                counts[month_key] += 1

    labels = []
    values = []
    for month_key in month_keys:
        try:
            label = datetime.datetime.strptime(month_key, "%Y-%m").strftime("%b")
        except ValueError:
            label = month_key
        labels.append(label)
        values.append(counts[month_key])
    return labels, values


def build_dashboard_context(user, role, data_label, students):
    total_students = len(students)
    total_sessions = sum(len(s.get("sessions", [])) for s in students)

    gender_data = _distribution(students, "gender")
    total_gender = sum(gender_data["values"]) if gender_data["values"] else 0
    distribution_rows = []
    for label, count in zip(gender_data["labels"], gender_data["values"]):
        percent = int(round((count / total_gender) * 100)) if total_gender else 0
        distribution_rows.append(
            {
                "label": label,
                "count": count,
                "percent": max(percent, 2 if count > 0 else 0),
            }
        )

    timeline_labels, timeline_values = _timeline_last_12_months(students)
    max_timeline = max(timeline_values) if timeline_values else 0
    timeline_bars = []
    for label, value in zip(timeline_labels, timeline_values):
        bar_height = int((value / max_timeline) * 170) if max_timeline > 0 else 4
        timeline_bars.append(
            {
                "label": label,
                "value": value,
                "height": max(bar_height, 4),
            }
        )

    return {
        "user": user,
        "role": role,
        "is_admin": role == "ADMIN",
        "data_label": data_label,
        "global_navbar": "",
        "total_students": total_students,
        "total_sessions": total_sessions,
        "distribution_rows": distribution_rows,
        "timeline_bars": timeline_bars,
    }
