import os
import json
import urllib.request
import datetime
import html
from pathlib import Path

USERNAME = os.getenv("GITHUB_USERNAME", "Dushyantcoder07")
TOKEN = os.getenv("GITHUB_API_TOKEN")

OUTPUT = Path("assets/github-dashboard.svg")

if not TOKEN:
  raise RuntimeError("GITHUB_API_TOKEN is not available.")

# ---------------------------------------------------------

# DATE RANGES

# ---------------------------------------------------------

now = datetime.datetime.now(datetime.timezone.utc)

year_start = datetime.datetime(
now.year,
1,
1,
tzinfo=datetime.timezone.utc
)

month_start = datetime.datetime(
now.year,
now.month,
1,
tzinfo=datetime.timezone.utc
)

def iso(dt):
  return dt.isoformat().replace("+00:00", "Z")

# ---------------------------------------------------------

# GITHUB GRAPHQL

# ---------------------------------------------------------

query = """
query(
$login: String!,
$yearFrom: DateTime!,
$monthFrom: DateTime!,
$to: DateTime!
) {
user(login: $login) {

year: contributionsCollection(
  from: $yearFrom,
  to: $to
) {
  totalCommitContributions
  totalIssueContributions
  totalPullRequestContributions
  totalPullRequestReviewContributions
  restrictedContributionsCount

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

month: contributionsCollection(
  from: $monthFrom,
  to: $to
) {
  totalCommitContributions

  contributionCalendar {
    totalContributions
  }
}

}
}
"""

payload = json.dumps(
{
"query": query,
"variables": {
"login": USERNAME,
"yearFrom": iso(year_start),
"monthFrom": iso(month_start),
"to": iso(now),
},
}
).encode()

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
  raise RuntimeError(
    json.dumps(result["errors"], indent=2)
  )

user = result["data"]["user"]

if not user:
  raise RuntimeError(
    f"GitHub user '{USERNAME}' was not found."
  )

year = user["year"]
month = user["month"]

calendar = year["contributionCalendar"]

# ---------------------------------------------------------

# STATISTICS

# ---------------------------------------------------------

month_commits = month["totalCommitContributions"]
month_contributions = month["contributionCalendar"]["totalContributions"]

year_commits = year["totalCommitContributions"]
year_contributions = calendar["totalContributions"]

pull_requests = year["totalPullRequestContributions"]
issues = year["totalIssueContributions"]
reviews = year["totalPullRequestReviewContributions"]

private_contributions = year["restrictedContributionsCount"]

days = []

for week in calendar["weeks"]:
  for day in week["contributionDays"]:
    days.append(
      {
        "date": day["date"],
        "count": day["contributionCount"],
      }
    )

active_days = sum(
1 for day in days
if day["count"] > 0
)

best_day = max(
(day["count"] for day in days),
default=0
)

# ---------------------------------------------------------

# CURRENT MONTH PROGRESS

# ---------------------------------------------------------

if now.month == 12:
  next_month = datetime.datetime(
    now.year + 1,
    1,
    1,
    tzinfo=datetime.timezone.utc
  )
else:
  next_month = datetime.datetime(
    now.year,
    now.month + 1,
    1,
    tzinfo=datetime.timezone.utc
  )

days_in_month = (next_month - month_start).days

month_progress = min(
100,
(now.day / days_in_month) * 100
)

# ---------------------------------------------------------

# CONTRIBUTION INTENSITY

# ---------------------------------------------------------

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

# ---------------------------------------------------------

# SVG HEATMAP

# ---------------------------------------------------------

CELL = 10
GAP = 3

graph_x = 47
graph_y = 440

heatmap = []

week_index = 0

for week in calendar["weeks"]:
    for day in week["contributionDays"]:
        date_value = datetime.date.fromisoformat(day["date"])
        weekday = date_value.weekday()
        weekday = (weekday + 1) % 7
        x = graph_x + week_index * (CELL + GAP)
        y = graph_y + weekday * (CELL + GAP)
        count = day["contributionCount"]
        color = contribution_color(count)
        title = html.escape(f"{count} contributions on {day['date']}")
        heatmap.append(
            f"""
            <g>
              <title>{title}</title>
              <rect
                x="{x}"
                y="{y}"
                width="{CELL}"
                height="{CELL}"
                rx="2.5"
                fill="{color}"
              />
            </g>
            """
        )
    week_index += 1

heatmap_svg = "\n".join(heatmap)

# ---------------------------------------------------------

# UTILITIES

# ---------------------------------------------------------

def safe(value):
  return html.escape(str(value))

updated = now.strftime(
"%d %b %Y • %H:%M UTC"
)

month_name = now.strftime("%B")

# ---------------------------------------------------------

# SVG

# ---------------------------------------------------------

svg = f"""
<svg
xmlns="http://www.w3.org/2000/svg"
width="1000"
height="610"
viewBox="0 0 1000 610"
role="img"
aria-labelledby="title description"

>

<title id="title">
Dushyant Singh Sisodiya GitHub Developer Activity
</title>

<desc id="description">
GitHub contribution statistics for {safe(USERNAME)}
</desc>

<defs>

<linearGradient
    id="background"
    x1="0"
    y1="0"
    x2="1"
    y2="1"
>
    <stop offset="0%" stop-color="#07111D"/>
    <stop offset="50%" stop-color="#0A1726"/>
    <stop offset="100%" stop-color="#071923"/>
</linearGradient>

<linearGradient
    id="accent"
    x1="0"
    y1="0"
    x2="1"
    y2="0"
>
    <stop offset="0%" stop-color="#14B8A6"/>
    <stop offset="50%" stop-color="#22D3EE"/>
    <stop offset="100%" stop-color="#0EA5E9"/>
</linearGradient>

<linearGradient
    id="card"
    x1="0"
    y1="0"
    x2="0"
    y2="1"
>
    <stop offset="0%" stop-color="#102131"/>
    <stop offset="100%" stop-color="#0B1724"/>
</linearGradient>

<filter
    id="glow"
    x="-50%"
    y="-50%"
    width="200%"
    height="200%"
>
    <feGaussianBlur
        stdDeviation="8"
        result="blur"
    />

    <feMerge>
        <feMergeNode in="blur"/>
        <feMergeNode in="SourceGraphic"/>
    </feMerge>
</filter>

</defs>

<!-- MAIN BACKGROUND -->

<rect
 width="1000"
 height="610"
 rx="28"
 fill="url(#background)"
/>

<!-- DECORATIVE GLOW -->

<circle
 cx="875"
 cy="40"
 r="130"
 fill="#0E7490"
 opacity="0.10"
/>

<circle
 cx="80"
 cy="570"
 r="130"
 fill="#14B8A6"
 opacity="0.06"
/>

<!-- TOP ACCENT -->

<rect
 x="28"
 y="25"
 width="944"
 height="4"
 rx="2"
 fill="url(#accent)"
/>

<!-- HEADER -->

<text
x="46"
y="78"
fill="#F8FAFC"
font-size="26"
font-weight="700"
font-family="Inter,Segoe UI,Arial,sans-serif"

>

Developer Activity

</text>

<text
x="46"
y="103"
fill="#64748B"
font-size="13"
font-family="Inter,Segoe UI,Arial,sans-serif"

>

@{safe(USERNAME)}  •  GitHub telemetry

</text>

<!-- LIVE INDICATOR -->

<circle
 cx="831"
 cy="75"
 r="5"
 fill="#2DD4BF"
 filter="url(#glow)"
/>

<text
x="846"
y="80"
fill="#94A3B8"
font-size="12"
font-family="Inter,Segoe UI,Arial,sans-serif"

>

AUTO UPDATED

</text>

<!-- CARD 1 -->

<rect
 x="45"
 y="135"
 width="210"
 height="118"
 rx="18"
 fill="url(#card)"
 stroke="#1E3347"
/>

<text
x="65"
y="165"
fill="#64748B"
font-size="11"
font-weight="600"
letter-spacing="1.2"
font-family="Inter,Segoe UI,Arial,sans-serif"

>

{month_name.upper()} COMMITS

</text>

<text
x="65"
y="213"
fill="#F8FAFC"
font-size="38"
font-weight="750"
font-family="Inter,Segoe UI,Arial,sans-serif"

>

{safe(month_commits)}

</text>

<text
x="65"
y="235"
fill="#2DD4BF"
font-size="11"
font-family="Inter,Segoe UI,Arial,sans-serif"

>

{safe(month_contributions)} total contributions

</text>

<!-- CARD 2 -->

<rect
 x="275"
 y="135"
 width="210"
 height="118"
 rx="18"
 fill="url(#card)"
 stroke="#1E3347"
/>

<text
x="295"
y="165"
fill="#64748B"
font-size="11"
font-weight="600"
letter-spacing="1.2"
font-family="Inter,Segoe UI,Arial,sans-serif"

>

{now.year} COMMITS

</text>

<text
x="295"
y="213"
fill="#F8FAFC"
font-size="38"
font-weight="750"
font-family="Inter,Segoe UI,Arial,sans-serif"

>

{safe(year_commits)}

</text>

<text
x="295"
y="235"
fill="#38BDF8"
font-size="11"
font-family="Inter,Segoe UI,Arial,sans-serif"

>

Commit contributions this year

</text>

<!-- CARD 3 -->

<rect
 x="505"
 y="135"
 width="210"
 height="118"
 rx="18"
 fill="url(#card)"
 stroke="#1E3347"
/>

<text
x="525"
y="165"
fill="#64748B"
font-size="11"
font-weight="600"
letter-spacing="1.2"
font-family="Inter,Segoe UI,Arial,sans-serif"

>

CONTRIBUTIONS

</text>

<text
x="525"
y="213"
fill="#F8FAFC"
font-size="38"
font-weight="750"
font-family="Inter,Segoe UI,Arial,sans-serif"

>

{safe(year_contributions)}

</text>

<text
x="525"
y="235"
fill="#2DD4BF"
font-size="11"
font-family="Inter,Segoe UI,Arial,sans-serif"

>

Across {safe(active_days)} active days

</text>

<!-- CARD 4 -->

<rect
 x="735"
 y="135"
 width="220"
 height="118"
 rx="18"
 fill="url(#card)"
 stroke="#1E3347"
/>

<text
x="755"
y="165"
fill="#64748B"
font-size="11"
font-weight="600"
letter-spacing="1.2"
font-family="Inter,Segoe UI,Arial,sans-serif"

>

PEAK ACTIVITY

</text>

<text
x="755"
y="213"
fill="#F8FAFC"
font-size="38"
font-weight="750"
font-family="Inter,Segoe UI,Arial,sans-serif"

>

{safe(best_day)}

</text>

<text
x="755"
y="235"
fill="#38BDF8"
font-size="11"
font-family="Inter,Segoe UI,Arial,sans-serif"

>

Contributions in one day

</text>

<!-- SECONDARY STATS -->

<rect
 x="45"
 y="278"
 width="910"
 height="83"
 rx="18"
 fill="#0B1724"
 stroke="#182C3D"
/>

<text
x="80"
y="309"
fill="#64748B"
font-size="10"
font-weight="600"
letter-spacing="1"
font-family="Inter,Segoe UI,Arial,sans-serif"

>

PULL REQUESTS

</text>

<text
x="80"
y="337"
fill="#E2E8F0"
font-size="22"
font-weight="700"
font-family="Inter,Segoe UI,Arial,sans-serif"

>

{safe(pull_requests)}

</text>

<text
x="285"
y="309"
fill="#64748B"
font-size="10"
font-weight="600"
letter-spacing="1"
font-family="Inter,Segoe UI,Arial,sans-serif"

>

ISSUES

</text>

<text
x="285"
y="337"
fill="#E2E8F0"
font-size="22"
font-weight="700"
font-family="Inter,Segoe UI,Arial,sans-serif"

>

{safe(issues)}

</text>

<text
x="445"
y="309"
fill="#64748B"
font-size="10"
font-weight="600"
letter-spacing="1"
font-family="Inter,Segoe UI,Arial,sans-serif"

>

REVIEWS

</text>

<text
x="445"
y="337"
fill="#E2E8F0"
font-size="22"
font-weight="700"
font-family="Inter,Segoe UI,Arial,sans-serif"

>

{safe(reviews)}

</text>

<text
x="605"
y="309"
fill="#64748B"
font-size="10"
font-weight="600"
letter-spacing="1"
font-family="Inter,Segoe UI,Arial,sans-serif"

>

ACTIVE DAYS

</text>

<text
x="605"
y="337"
fill="#E2E8F0"
font-size="22"
font-weight="700"
font-family="Inter,Segoe UI,Arial,sans-serif"

>

{safe(active_days)}

</text>

<text
x="785"
y="309"
fill="#64748B"
font-size="10"
font-weight="600"
letter-spacing="1"
font-family="Inter,Segoe UI,Arial,sans-serif"

>

PRIVATE ACTIVITY

</text>

<text
x="785"
y="337"
fill="#E2E8F0"
font-size="22"
font-weight="700"
font-family="Inter,Segoe UI,Arial,sans-serif"

>

{safe(private_contributions)}

</text>

<!-- GRAPH HEADING -->

<text
x="45"
y="405"
fill="#F1F5F9"
font-size="16"
font-weight="700"
font-family="Inter,Segoe UI,Arial,sans-serif"

>

{now.year} Contribution Matrix

</text>

<text
x="955"
y="405"
text-anchor="end"
fill="#64748B"
font-size="11"
font-family="Inter,Segoe UI,Arial,sans-serif"

>

{safe(year_contributions)} contributions

</text>

<!-- CONTRIBUTION HEATMAP -->

{heatmap_svg}

<!-- LEGEND -->

<text
x="45"
y="555"
fill="#64748B"
font-size="10"
font-family="Inter,Segoe UI,Arial,sans-serif"

>

LESS

</text>

<rect x="80" y="546" width="10" height="10" rx="2" fill="#132131"/>
<rect x="96" y="546" width="10" height="10" rx="2" fill="#0E4F50"/>
<rect x="112" y="546" width="10" height="10" rx="2" fill="#0F766E"/>
<rect x="128" y="546" width="10" height="10" rx="2" fill="#14B8A6"/>
<rect x="144" y="546" width="10" height="10" rx="2" fill="#5EEAD4"/>

<text
x="162"
y="555"
fill="#64748B"
font-size="10"
font-family="Inter,Segoe UI,Arial,sans-serif"

>

MORE

</text>

<!-- FOOTER -->

<line
 x1="45"
 y1="578"
 x2="955"
 y2="578"
 stroke="#182C3D"
/>

<text
x="45"
y="597"
fill="#475569"
font-size="10"
font-family="Inter,Segoe UI,Arial,sans-serif"

>

Generated from GitHub GraphQL API

</text>

<text
x="955"
y="597"
text-anchor="end"
fill="#475569"
font-size="10"
font-family="Inter,Segoe UI,Arial,sans-serif"

>

Updated {safe(updated)}

</text>

</svg>
"""

OUTPUT.parent.mkdir(
parents=True,
exist_ok=True
)

OUTPUT.write_text(
svg,
encoding="utf-8"
)

print(
f"Dashboard generated: {OUTPUT}"
)

print(
f"Month commits: {month_commits}"
)

print(
f"Year commits: {year_commits}"
)

print(
f"Year contributions: {year_contributions}"
)
