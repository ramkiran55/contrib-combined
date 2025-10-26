\
import os
import sys
import requests
from datetime import datetime, timedelta

GH_TOKEN = os.getenv("GH_TOKEN")
USER_1 = os.getenv("USER_1")
USER_2 = os.getenv("USER_2")
OUTPUT_PATH = os.getenv("OUTPUT_PATH", "assets/combined-heatmap.svg")

GRAPHQL_URL = "https://api.github.com/graphql"

QUERY = """
query($login:String!) {
  user(login:$login) {
    contributionsCollection {
      contributionCalendar {
        totalContributions
        weeks {
          contributionDays {
            date
            contributionCount
          }
        }
      }
    }
  }
}
"""

def fetch_calendar(login: str):
    headers = {"Authorization": f"Bearer {GH_TOKEN}"}
    resp = requests.post(GRAPHQL_URL, json={"query": QUERY, "variables": {"login": login}}, headers=headers, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    if "errors" in data:
        raise RuntimeError(f"GraphQL errors for {login}: {data['errors']}")
    weeks = data["data"]["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]
    days = []
    for w in weeks:
        for d in w["contributionDays"]:
            days.append((d["date"], int(d["contributionCount"])))
    return days

def combine_days(days1, days2):
    # Build dict date->count
    counts = {}
    for dt, c in days1:
        counts[dt] = counts.get(dt, 0) + c
    for dt, c in days2:
        counts[dt] = counts.get(dt, 0) + c
    # Sort by date
    return sorted(counts.items(), key=lambda x: x[0])

def to_svg(day_counts):
    # Simple square grid like GitHub's (7 rows x N columns)
    # Determine start date (Sunday) to align like GitHub
    if not day_counts:
        return "<svg xmlns='http://www.w3.org/2000/svg' width='100' height='20'></svg>"
    dates = [datetime.fromisoformat(d) for d, _ in day_counts]
    min_date = min(dates)
    # Shift back to previous Sunday
    start = min_date - timedelta(days=min_date.weekday() + 1) if min_date.weekday() != 6 else min_date
    # Create continuous range until max date
    max_date = max(dates)
    days = []
    cur = start
    while cur <= max_date:
        days.append(cur.date().isoformat())
        cur += timedelta(days=1)

    # build a map for quick lookup
    value_map = {d: c for d, c in day_counts}

    # Color scale thresholds similar-ish to GitHub
    # 0, 1-3, 4-7, 8-15, 16+
    def level(v):
        if v <= 0: return 0
        if v <= 3: return 1
        if v <= 7: return 2
        if v <= 15: return 3
        return 4

    # color palette (GitHub-like but neutral)
    palette = ["#ebedf0", "#9be9a8", "#40c463", "#30a14e", "#216e39"]

    cols = (len(days) + 6) // 7
    cell = 11  # size including gap
    size = 10  # square size
    gap = 1
    width = cols * cell + 30
    height = 7 * cell + 20

    svg = [f"<svg xmlns='http://www.w3.org/2000/svg' width='{width}' height='{height}' viewBox='0 0 {width} {height}'>"]
    svg.append("<g transform='translate(15,10)'>")

    for idx, date_str in enumerate(days):
        col = idx // 7
        row = idx % 7
        x = col * cell
        y = row * cell
        v = value_map.get(date_str, 0)
        color = palette[level(v)]
        svg.append(f"<rect x='{x}' y='{y}' width='{size}' height='{size}' rx='2' ry='2' fill='{color}'>")
        svg.append(f"<title>{date_str}: {v} contributions</title></rect>")

    svg.append("</g>")
    svg.append("</svg>")
    return "\n".join(svg)

def main():
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    if not GH_TOKEN:
        print("GH_TOKEN not set", file=sys.stderr)
        sys.exit(1)
    if not USER_1 or not USER_2:
        print("USER_1/USER_2 not set", file=sys.stderr)
        sys.exit(1)

    days1 = fetch_calendar(USER_1)
    days2 = fetch_calendar(USER_2)
    combined = combine_days(days1, days2)
    svg = to_svg(combined)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        f.write(svg)
    print(f"Wrote {OUTPUT_PATH}")

if __name__ == "__main__":
    main()
