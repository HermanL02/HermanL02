"""Write Wakapi coding stats into README.md between the waka markers."""
import base64, json, os, re, urllib.request

BASE = "https://codetime.hermanyiqunliang.com/api/compat/wakatime/v1"
RANGE = "all_time"
IGNORED = {"Unknown", "Text", "Other"}
TOP_N = 6
BAR = 25
ALIASES = {"Github-estimate": "Claude code"}

key = os.environ["WAKAPI_API_KEY"]
req = urllib.request.Request(
    f"{BASE}/users/current/stats/{RANGE}",
    headers={"Authorization": "Basic " + base64.b64encode(key.encode()).decode()},
)
data = json.load(urllib.request.urlopen(req, timeout=30))["data"]

def bar(pct):
    filled = round(pct / 100 * BAR)
    return "█" * filled + "░" * (BAR - filled)

def merge(items):
    """Fold aliased names into their target and recompute text/percent."""
    totals = {}
    for i in items:
        name = ALIASES.get(i["name"], i["name"])
        totals[name] = totals.get(name, 0) + float(i["total_seconds"])
    grand = sum(totals.values()) or 1
    out = []
    for name, secs in sorted(totals.items(), key=lambda kv: -kv[1]):
        h, m = divmod(int(secs) // 60, 60)
        out.append({"name": name, "text": f"{h} hrs {m} mins", "percent": secs / grand * 100})
    return out

def section(title, items):
    items = merge(items)
    items = [i for i in items if i["name"] not in IGNORED and i["percent"] >= 0.1][:TOP_N]
    if not items:
        return ""
    width = max(len(i["name"]) for i in items)
    tw = max(len(i["text"]) for i in items)
    rows = [
        f"{i['name']:<{width}}  {i['text']:>{tw}}  {bar(i['percent'])}  {i['percent']:5.1f} %"
        for i in items
    ]
    return f"{title}\n" + "\n".join(rows) + "\n"

parts = [f"Total: {data['human_readable_total']}  ·  Daily avg: {data.get('human_readable_daily_average', 'n/a')}\n"]
parts.append(section("💬 Languages", data.get("languages", [])))
parts.append(section("🛠️ Editors", data.get("editors", [])))
block = "\n".join(p for p in parts if p)

readme = open("README.md", encoding="utf-8").read()
new = re.sub(
    r"(<!--START_SECTION:waka-->).*?(<!--END_SECTION:waka-->)",
    lambda m: f"{m.group(1)}\n\n```txt\n{block}```\n\n{m.group(2)}",
    readme,
    flags=re.S,
)
open("README.md", "w", encoding="utf-8").write(new)
