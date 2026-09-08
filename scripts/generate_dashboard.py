import datetime
import html
import json
import os
import urllib.request
from pathlib import Path


USERNAME = os.getenv("GITHUB_USERNAME", "Dushyantcoder07")
TOKEN = os.getenv("GITHUB_API_TOKEN")
OUTPUT = Path("assets/github-dashboard.svg")


def iso(value):
    return value.isoformat().replace("+00:00", "Z")


def contribution_color(count):
    if count == 0:
        return "#132131"
    if count <= 2:
        return "#0E4F50"
    if count <= 5:
        return "#0F766E"
    if count <= 9:
        return "#14B8A6"
    return "#5EEAD4"


def safe(value):
    return html.escape(str(value))


def fetch_github_data(now, year_start, month_start):
    query = """
    query($login: String!, $yearFrom: DateTime!, $monthFrom: DateTime!, $to: DateTime!) {
      user(login: $login) {
        year: contributionsCollection(from: $yearFrom, to: $to) {
          totalCommitContributions
          totalIssueContributions
          totalPullRequestContributions
          totalPullRequestReviewContributions
          restrictedContributionsCount
          contributionCalendar {
            totalContributions
            weeks {
              contributionDays { date contributionCount }
            }
          }
        }
        month: contributionsCollection(from: $monthFrom, to: $to) {
          totalCommitContributions
          contributionCalendar { totalContributions }
        }
      }
    }
    """
    payload = json.dumps({
        "query": query,
        "variables": {
            "login": USERNAME,
            "yearFrom": iso(year_start),
            "monthFrom": iso(month_start),
            "to": iso(now),
        },
    }).encode()
    request = urllib.request.Request(
        "https://api.github.com/graphql",
        data=payload,
        headers={
            "Authorization": f"Bearer {TOKEN}",
            "Content-Type": "application/json",
            "User-Agent": "Dushyantcoder07-profile-dashboard",
        },
    )
    with urllib.request.urlopen(request) as response:
        result = json.loads(response.read().decode())
    if result.get("errors"):
        raise RuntimeError(json.dumps(result["errors"], indent=2))
    user = result["data"]["user"]
    if not user:
        raise RuntimeError(f"GitHub user '{USERNAME}' was not found.")
    return user


def build_heatmap(calendar):
    cells = []
    for week_index, week in enumerate(calendar["weeks"]):
        for day in week["contributionDays"]:
            date_value = datetime.date.fromisoformat(day["date"])
            weekday = (date_value.weekday() + 1) % 7
            x = 47 + week_index * 13
            y = 440 + weekday * 13
            count = day["contributionCount"]
            title = safe(f"{count} contributions on {day['date']}")
            cells.append(
                f'<g><title>{title}</title><rect x="{x}" y="{y}" '
                f'width="10" height="10" rx="2.5" fill="{contribution_color(count)}" /></g>'
            )
    return "\n".join(cells)


def build_svg(user, now):
    year = user["year"]
    month = user["month"]
    calendar = year["contributionCalendar"]
    days = [
        day
        for week in calendar["weeks"]
        for day in week["contributionDays"]
    ]
    month_name = now.strftime("%B")
    active_days = sum(day["contributionCount"] > 0 for day in days)
    best_day = max((day["contributionCount"] for day in days), default=0)
    updated = now.strftime("%d %b %Y - %H:%M UTC")
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="1000" height="610" viewBox="0 0 1000 610" role="img" aria-labelledby="title description">
<title id="title">Dushyant Singh Sisodiya GitHub Developer Activity</title>
<desc id="description">GitHub contribution statistics for {safe(USERNAME)}</desc>
<defs>
  <linearGradient id="background" x1="0" y1="0" x2="1" y2="1"><stop offset="0%" stop-color="#07111D"/><stop offset="50%" stop-color="#0A1726"/><stop offset="100%" stop-color="#071923"/></linearGradient>
  <linearGradient id="accent" x1="0" y1="0" x2="1" y2="0"><stop offset="0%" stop-color="#14B8A6"/><stop offset="50%" stop-color="#22D3EE"/><stop offset="100%" stop-color="#0EA5E9"/></linearGradient>
  <linearGradient id="card" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stop-color="#102131"/><stop offset="100%" stop-color="#0B1724"/></linearGradient>
</defs>
<rect width="1000" height="610" rx="28" fill="url(#background)"/>
<rect x="28" y="25" width="944" height="4" rx="2" fill="url(#accent)"/>
<text x="46" y="78" fill="#F8FAFC" font-size="26" font-weight="700" font-family="Inter,Segoe UI,Arial,sans-serif">Developer Activity</text>
<text x="46" y="103" fill="#64748B" font-size="13" font-family="Inter,Segoe UI,Arial,sans-serif">@{safe(USERNAME)} - GitHub telemetry</text>
<text x="846" y="80" fill="#94A3B8" font-size="12" font-family="Inter,Segoe UI,Arial,sans-serif">AUTO UPDATED</text>
<rect x="45" y="135" width="910" height="118" rx="18" fill="url(#card)" stroke="#1E3347"/>
<text x="70" y="170" fill="#64748B" font-size="11" font-weight="600" font-family="Inter,Segoe UI,Arial,sans-serif">{month_name.upper()} COMMITS</text>
<text x="70" y="220" fill="#F8FAFC" font-size="38" font-weight="700" font-family="Inter,Segoe UI,Arial,sans-serif">{month["totalCommitContributions"]}</text>
<text x="70" y="240" fill="#2DD4BF" font-size="11" font-family="Inter,Segoe UI,Arial,sans-serif">{month["contributionCalendar"]["totalContributions"]} total contributions</text>
<text x="300" y="170" fill="#64748B" font-size="11" font-weight="600" font-family="Inter,Segoe UI,Arial,sans-serif">{now.year} COMMITS</text>
<text x="300" y="220" fill="#F8FAFC" font-size="38" font-weight="700" font-family="Inter,Segoe UI,Arial,sans-serif">{year["totalCommitContributions"]}</text>
<text x="300" y="240" fill="#38BDF8" font-size="11" font-family="Inter,Segoe UI,Arial,sans-serif">Commit contributions this year</text>
<text x="530" y="170" fill="#64748B" font-size="11" font-weight="600" font-family="Inter,Segoe UI,Arial,sans-serif">CONTRIBUTIONS</text>
<text x="530" y="220" fill="#F8FAFC" font-size="38" font-weight="700" font-family="Inter,Segoe UI,Arial,sans-serif">{calendar["totalContributions"]}</text>
<text x="530" y="240" fill="#2DD4BF" font-size="11" font-family="Inter,Segoe UI,Arial,sans-serif">Across {active_days} active days</text>
<text x="760" y="170" fill="#64748B" font-size="11" font-weight="600" font-family="Inter,Segoe UI,Arial,sans-serif">PEAK ACTIVITY</text>
<text x="760" y="220" fill="#F8FAFC" font-size="38" font-weight="700" font-family="Inter,Segoe UI,Arial,sans-serif">{best_day}</text>
<text x="760" y="240" fill="#38BDF8" font-size="11" font-family="Inter,Segoe UI,Arial,sans-serif">Contributions in one day</text>
<rect x="45" y="278" width="910" height="83" rx="18" fill="#0B1724" stroke="#182C3D"/>
<text x="80" y="320" fill="#64748B" font-size="10" font-family="Inter,Segoe UI,Arial,sans-serif">PULL REQUESTS  {year["totalPullRequestContributions"]}    ISSUES  {year["totalIssueContributions"]}    REVIEWS  {year["totalPullRequestReviewContributions"]}    PRIVATE ACTIVITY  {year["restrictedContributionsCount"]}</text>
<text x="45" y="405" fill="#F1F5F9" font-size="16" font-weight="700" font-family="Inter,Segoe UI,Arial,sans-serif">{now.year} Contribution Matrix</text>
<text x="955" y="405" text-anchor="end" fill="#64748B" font-size="11" font-family="Inter,Segoe UI,Arial,sans-serif">{calendar["totalContributions"]} contributions</text>
{build_heatmap(calendar)}
<text x="45" y="555" fill="#64748B" font-size="10" font-family="Inter,Segoe UI,Arial,sans-serif">LESS</text>
<rect x="80" y="546" width="10" height="10" rx="2" fill="#132131"/><rect x="96" y="546" width="10" height="10" rx="2" fill="#0E4F50"/><rect x="112" y="546" width="10" height="10" rx="2" fill="#0F766E"/><rect x="128" y="546" width="10" height="10" rx="2" fill="#14B8A6"/><rect x="144" y="546" width="10" height="10" rx="2" fill="#5EEAD4"/>
<text x="162" y="555" fill="#64748B" font-size="10" font-family="Inter,Segoe UI,Arial,sans-serif">MORE</text>
<line x1="45" y1="578" x2="955" y2="578" stroke="#182C3D"/>
<text x="45" y="597" fill="#475569" font-size="10" font-family="Inter,Segoe UI,Arial,sans-serif">Generated from GitHub GraphQL API</text>
<text x="955" y="597" text-anchor="end" fill="#475569" font-size="10" font-family="Inter,Segoe UI,Arial,sans-serif">Updated {updated}</text>
</svg>"""


def main():
    if not TOKEN:
        raise RuntimeError("GITHUB_API_TOKEN is not available.")
    now = datetime.datetime.now(datetime.timezone.utc)
    year_start = datetime.datetime(now.year, 1, 1, tzinfo=datetime.timezone.utc)
    month_start = datetime.datetime(now.year, now.month, 1, tzinfo=datetime.timezone.utc)
    user = fetch_github_data(now, year_start, month_start)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(build_svg(user, now), encoding="utf-8")
    print(f"Dashboard generated: {OUTPUT}")


if __name__ == "__main__":
    main()
