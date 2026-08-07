from collections import Counter
import datetime
import json


DASHBOARD_WEB_TEMPLATE = """
<!doctype html>
<html>
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Dashboard</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
      :root {
        --bg: #f3f4f6;
        --card: #ffffff;
        --text: #111827;
        --muted: #6b7280;
        --blue: #2563eb;
        --green: #16a34a;
      }
      * { box-sizing: border-box; }
      body {
        margin: 0;
        font-family: Arial, sans-serif;
        background: var(--bg);
        color: var(--text);
      }
      .wrap {
        max-width: 1200px;
        margin: 24px auto;
        padding: 0 16px 24px;
      }
      .topbar {
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        gap: 12px;
        flex-wrap: wrap;
      }
      .title { margin: 0; font-size: 34px; }
      .meta { color: var(--muted); margin: 4px 0; }
      .links { margin-top: 8px; }
      .links a { margin-right: 10px; }
      .admin-btn {
        display: inline-block;
        margin-top: 10px;
        padding: 8px 12px;
        border-radius: 8px;
        background: #1f2937;
        color: white;
        text-decoration: none;
      }
      .stats {
        margin-top: 18px;
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
        gap: 14px;
      }
      .card {
        background: var(--card);
        border-radius: 14px;
        padding: 16px;
        box-shadow: 0 8px 20px rgba(0,0,0,0.06);
      }
      .stat-label { color: var(--muted); font-size: 13px; }
      .stat-value { font-size: 34px; font-weight: 700; margin-top: 4px; }
      .charts {
        margin-top: 18px;
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 14px;
      }
      .chart-card h3 { margin-top: 0; margin-bottom: 12px; }
      .filters {
        display: flex;
        gap: 8px;
        flex-wrap: wrap;
        margin-bottom: 10px;
      }
      select {
        padding: 8px 10px;
        border-radius: 8px;
        border: 1px solid #d1d5db;
        background: white;
      }
      @media (max-width: 920px) {
        .charts { grid-template-columns: 1fr; }
      }
    </style>
  </head>
  <body>
    <div class="wrap">
      <div class="topbar">
        <div>
          <h1 class="title">Overview & Analytics</h1>
          <p class="meta">Welcome, {{ user }}.</p>
          <p class="meta">Role: {{ role }} | Viewing {{ data_label }}.</p>
          <div class="links">
            <a href="/">Home</a>
            <a href="/infrastructure">Infrastructure</a>
            {% if is_admin %}<a href="/user-roles">User Roles</a>{% endif %}
            <a href="/logout">Logout</a>
          </div>
          {% if is_admin %}<a class="admin-btn" href="/user-roles">Open Admin Items</a>{% endif %}
        </div>
      </div>

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
          <h3>Distribution Profiles</h3>
          <div class="filters">
            <label for="distributionType">View:</label>
            <select id="distributionType">
              <option value="gender">Gender</option>
              <option value="ethnicity">Ethnicity</option>
              <option value="referral">Referral Type</option>
            </select>
          </div>
          <canvas id="distributionChart" height="250"></canvas>
        </div>

        <div class="card chart-card">
          <h3>Session Tracking Timeline</h3>
          <canvas id="timelineChart" height="250"></canvas>
        </div>
      </div>
    </div>

    <script>
      const distributionData = {{ distribution_data_json|safe }};
      const timelineLabels = {{ timeline_labels_json|safe }};
      const timelineValues = {{ timeline_values_json|safe }};

      const palette = [
        '#3b82f6', '#22c55e', '#ec4899', '#f59e0b', '#8b5cf6',
        '#06b6d4', '#ef4444', '#84cc16', '#0ea5e9', '#f97316'
      ];

      const distributionCtx = document.getElementById('distributionChart').getContext('2d');
      const timelineCtx = document.getElementById('timelineChart').getContext('2d');

      function buildDistributionDataset(key) {
        const labels = distributionData[key].labels;
        const values = distributionData[key].values;
        const colors = labels.map((_, i) => palette[i % palette.length]);
        return { labels, values, colors };
      }

      let currentDistribution = buildDistributionDataset('gender');

      const distributionChart = new Chart(distributionCtx, {
        type: 'bar',
        data: {
          labels: currentDistribution.labels,
          datasets: [{
            label: 'Students',
            data: currentDistribution.values,
            backgroundColor: currentDistribution.colors
          }]
        },
        options: {
          responsive: true,
          plugins: { legend: { display: false } },
          scales: { y: { beginAtZero: true, ticks: { precision: 0 } } }
        }
      });

      new Chart(timelineCtx, {
        type: 'line',
        data: {
          labels: timelineLabels,
          datasets: [{
            label: 'Sessions',
            data: timelineValues,
            borderColor: '#16a34a',
            backgroundColor: 'rgba(22,163,74,0.18)',
            fill: true,
            tension: 0.25
          }]
        },
        options: {
          responsive: true,
          scales: { y: { beginAtZero: true, ticks: { precision: 0 } } }
        }
      });

      document.getElementById('distributionType').addEventListener('change', (event) => {
        const map = {
          gender: 'gender',
          ethnicity: 'ethnicity',
          referral: 'referral'
        };
        currentDistribution = buildDistributionDataset(map[event.target.value]);
        distributionChart.data.labels = currentDistribution.labels;
        distributionChart.data.datasets[0].data = currentDistribution.values;
        distributionChart.data.datasets[0].backgroundColor = currentDistribution.colors;
        distributionChart.update();
      });
    </script>
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
        d = (now.replace(day=1) - datetime.timedelta(days=i * 30))
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
            label = datetime.datetime.strptime(month_key, "%Y-%m").strftime("%b %y")
        except ValueError:
            label = month_key
        labels.append(label)
        values.append(counts[month_key])
    return labels, values


def build_dashboard_context(user, role, data_label, students):
    total_students = len(students)
    total_sessions = sum(len(s.get("sessions", [])) for s in students)

    distribution_data = {
        "gender": _distribution(students, "gender"),
        "ethnicity": _distribution(students, "ethnicity"),
        "referral": _distribution(students, "referral_type"),
    }

    timeline_labels, timeline_values = _timeline_last_12_months(students)

    return {
        "user": user,
        "role": role,
        "is_admin": role == "ADMIN",
        "data_label": data_label,
        "total_students": total_students,
        "total_sessions": total_sessions,
        "distribution_data_json": json.dumps(distribution_data),
        "timeline_labels_json": json.dumps(timeline_labels),
        "timeline_values_json": json.dumps(timeline_values),
    }
