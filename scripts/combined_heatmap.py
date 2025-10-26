\
import os
import sys
import math
import requests
from datetime import datetime, date, timedelta
from collections import defaultdict

GRAPHQL_URL = "https://api.github.com/graphql"
GH_TOKEN = os.getenv("GH_TOKEN")
USER_1 = os.getenv("USER_1")
USER_2 = os.getenv("USER_2")
OUTPUT_PATH = os.getenv("OUTPUT_PATH", "assets/combined-heatmap.svg")

CELL_SIZE = int(os.getenv("CELL_SIZE", "9"))
CELL_GAP  = int(os.getenv("CELL_GAP", "1"))
RADIUS    = 2

USER_CREATED_QUERY = """
query($login:String!) {
  user(login:$login) {
    createdAt
  }
}
"""

CALENDAR_RANGE_QUERY = """
query($login:String!, $from:DateTime!, $to:DateTime!) {
  user(login:$login) {
    contributionsCollection(from:$from, to:$to) {
      contributionCalendar {
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

def gh_post(query: str, variables: dict):
    headers = {"Authorization": f"Bearer {GH_TOKEN}"}
    r = requests.post(GRAPHQL_URL, json={"query": query, "variables": variables}, headers=headers, timeout=45)
    r.raise_for_status()
    data = r.json()
    if "errors" in data and data["errors"]:
        raise RuntimeError(f"GitHub GraphQL error: {data['errors']}")
    return data

def get_created_at(login: str) -> datetime:
    data = gh_post(USER_CREATED_QUERY, {"login": login})
    iso = data["data"]["user"]["createdAt"]
    return datetime.fromisoformat(iso.replace("Z", "+00:00"))

def daterange_chunks(start: date, end: date, days_per_chunk=365):
    cur = start
    while cur <= end:
        chunk_end = min(end, cur + timedelta(days=days_per_chunk))
        yield (datetime.combine(cur, datetime.min.time()), datetime.combine(chunk_end, datetime.max.time()))
        cur = chunk_end + timedelta(days=1)

def fetch_calendar_range(login: str, start: date, end: date):
    all_days = []
    for f,t in daterange_chunks(start, end, 365):
        data = gh_post(CALENDAR_RANGE_QUERY, {"login": login, "from": f.isoformat(), "to": t.isoformat()})
        weeks = data["data"]["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]
        for w in weeks:
            for d in w["contributionDays"]:
                all_days.append((d["date"], int(d["contributionCount"])))
    return all_days

def combine_users(u1_days, u2_days):
    m = defaultdict(int)
    for d, c in u1_days:
        m[d] += c
    for d, c in u2_days:
        m[d] += c
    return sorted(m.items(), key=lambda x: x[0])

def previous_sunday(dt: date) -> date:
    return dt - timedelta(days=(dt.weekday()+1) % 7)

def build_year_block_svg(year: int, values_map: dict):
    year_start = date(year, 1, 1)
    year_end   = date(year, 12, 31)
    start_aligned = previous_sunday(year_start)

    days = []
    cur = start_aligned
    while cur <= year_end:
        days.append(cur)
        cur += timedelta(days=1)

    cols = (len(days) + 6) // 7
    cell = CELL_SIZE + CELL_GAP
    left_margin = 50
    top_margin = 18
    width = left_margin + cols * cell + 10
    height = top_margin + 7 * cell + 6

    out = [f"<svg xmlns='http://www.w3.org/2000/svg' width='{width}' height='{height}' viewBox='0 0 {width} {height}'>"]
    out.append(f"<text x='5' y='{top_margin}' font-size='12' font-family='sans-serif' fill='#57606a'>{year}</text>")
    out.append(f"<g transform='translate({left_margin},{top_margin})'>")

    for idx, dt in enumerate(days):
        col = idx // 7
        row = idx % 7
        x = col * cell
        y = row * cell
        v = values_map.get(dt.isoformat(), 0)
        colr = "#ebedf0" if v <= 0 else ("#9be9a8" if v <= 3 else ("#40c463" if v <= 7 else ("#30a14e" if v <= 15 else "#216e39")))
        out.append(f"<rect x='{x}' y='{y}' width='{CELL_SIZE}' height='{CELL_SIZE}' rx='2' ry='2' fill='{colr}'>")
        out.append(f"<title>{dt.isoformat()}: {v} contributions</title></rect>")

    out.append("</g></svg>")
    return "\n".join(out), width, height

def assemble_stacked_svg(year_svgs):
    padding = 6
    total_w = max(w for _,w,_ in year_svgs) if year_svgs else 100
    total_h = sum(h for _,_,h in year_svgs) + padding * (len(year_svgs)-1 if year_svgs else 0)
    out = [f"<svg xmlns='http://www.w3.org/2000/svg' width='{total_w}' height='{total_h}' viewBox='0 0 {total_w} {total_h}'>"]
    y = 0
    for svg, w, h in year_svgs:
        inner = svg.split(">", 1)[1].rsplit("</svg>", 1)[0]
        out.append(f"<g transform='translate(0,{y})'>{inner}</g>")
        y += h + padding
    out.append("</svg>")
    return "\n".join(out)

def main():
    if not GH_TOKEN:
        print("GH_TOKEN not set", file=sys.stderr)
        sys.exit(1)
    if not USER_1 or not USER_2:
        print("USER_1/USER_2 not set", file=sys.stderr)
        sys.exit(1)

    u1_created = get_created_at(USER_1).date()
    u2_created = get_created_at(USER_2).date()
    today = datetime.utcnow().date()

    u1_days = fetch_calendar_range(USER_1, u1_created, today)
    u2_days = fetch_calendar_range(USER_2, u2_created, today)

    combined = combine_users(u1_days, u2_days)

    by_year = defaultdict(dict)
    for d_iso, count in combined:
        y = datetime.fromisoformat(d_iso).year
        by_year[y][d_iso] = count

    year_svgs = []
    for year in sorted(by_year.keys()):
        svg, w, h = build_year_block_svg(year, by_year[year])
        year_svgs.append((svg, w, h))

    final_svg = assemble_stacked_svg(year_svgs)
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        f.write(final_svg)
    print(f"Wrote {OUTPUT_PATH}")

if __name__ == "__main__":
    main()
