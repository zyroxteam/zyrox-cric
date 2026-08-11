#!/usr/bin/env python3
# ============================================================================
#  ZYROX CRICBUZZ — Live Cricket Scores & Scorecards CLI
#  Reverse-engineered from cricbuzz.com (Next.js RSC payload extraction)
#
#  Works on: Termux, Linux, macOS, Windows (Python 3.8+)
#  Dependencies: NONE (stdlib only)
#
#  Educational / personal use only. CricBuzz ke data ko thoda rehmat se use
#  karo — no bulk scraping, no reselling.
# ============================================================================
import json
import re
import sys
import time
import urllib.request
import urllib.parse
from datetime import datetime

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36")
BASE = "https://www.cricbuzz.com"

# ----------------------------------------------------------------------------
# Colors
# ----------------------------------------------------------------------------
C = {
    "reset": "\033[0m", "bold": "\033[1m", "dim": "\033[2m",
    "cyan": "\033[96m", "pink": "\033[95m", "violet": "\033[35m",
    "gold": "\033[93m", "green": "\033[92m", "red": "\033[91m",
    "blue": "\033[94m",
}
NO_COLOR = os_environ_check = False


def c(code, text=""):
    if NO_COLOR:
        return text
    return f"{C.get(code, '')}{text}{C['reset']}"


def os_environ_check():
    return False


# ----------------------------------------------------------------------------
# HTTP + RSC payload extraction
# ----------------------------------------------------------------------------
def fetch(url, timeout=25):
    req = urllib.request.Request(url, headers={
        "User-Agent": UA,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    })
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8", errors="ignore")


def js_unescape(s):
    """Decode JS string literal escapes (one level)."""
    out, i, n = [], 0, len(s)
    while i < n:
        ch = s[i]
        if ch == "\\" and i + 1 < n:
            nxt = s[i + 1]
            if nxt == "u" and i + 5 < n:
                try:
                    out.append(chr(int(s[i + 2:i + 6], 16)))
                    i += 6
                    continue
                except ValueError:
                    pass
            mp = {"n": "\n", "t": "\t", "r": "\r", '"': '"', "'": "'",
                  "\\": "\\", "/": "/", "b": "\b", "f": "\f"}
            if nxt in mp:
                out.append(mp[nxt])
                i += 2
                continue
            out.append(nxt)
            i += 2
            continue
        out.append(ch)
        i += 1
    return "".join(out)


def rsc_data(html):
    """Extract + fully unescape Next.js RSC payload streams (double-escaped)."""
    streams = re.findall(r'__next_f\.push\(\[1,"((?:[^"\\]|\\.)*)"\]\)', html)
    data = "".join(js_unescape(s) for s in streams)
    return js_unescape(data)


def extract_json(data, anchor):
    """anchor ke baad balanced JSON object/array extract karo."""
    i = data.find(anchor)
    if i < 0:
        return None
    start = i + len(anchor)
    while start < len(data) and data[start] in " \n\t:":
        start += 1
    if start >= len(data) or data[start] not in "{[":
        return None
    stack, in_str, esc = [], False, False
    for j in range(start, len(data)):
        ch = data[j]
        if in_str:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == '"':
                in_str = False
        else:
            if ch == '"':
                in_str = True
            elif ch in "{[":
                stack.append(ch)
            elif ch in "}]":
                stack.pop()
                if not stack:
                    return data[start:j + 1]
    return None


# ----------------------------------------------------------------------------
# Data helpers
# ----------------------------------------------------------------------------
def fmt_ts(ms):
    try:
        return datetime.fromtimestamp(ms / 1000).strftime("%d %b %Y, %I:%M %p")
    except Exception:
        return "?"


def score_str(team_score):
    inngs = (team_score or {}).get("inngs1") or {}
    runs = inngs.get("runs")
    if runs is None:
        return ""
    wkts = inngs.get("wickets", 0)
    ov = inngs.get("overs", 0)
    txt = f"{runs}/{wkts}"
    if ov:
        txt += f" ({ov}ov)"
    return txt


def get_match_summary(match):
    """match dict (matchesList item) -> printable summary dict."""
    m = match.get("match", match)
    mi = m.get("matchInfo", {})
    ms = m.get("matchScore", {})
    t1 = mi.get("team1", {}).get("teamSName", "?")
    t2 = mi.get("team2", {}).get("teamSName", "?")
    s1 = score_str(ms.get("team1Score"))
    s2 = score_str(ms.get("team2Score"))
    return {
        "id": mi.get("matchId"),
        "series": mi.get("seriesName", ""),
        "desc": mi.get("matchDesc", ""),
        "format": mi.get("matchFormat", ""),
        "state": mi.get("state", ""),
        "status": mi.get("status", ""),
        "t1": t1, "t2": t2, "s1": s1, "s2": s2,
        "venue": f"{mi.get('venueInfo', {}).get('ground', '')}, {mi.get('venueInfo', {}).get('city', '')}",
        "start": fmt_ts(mi.get("startDate")),
    }


# ----------------------------------------------------------------------------
# Commands
# ----------------------------------------------------------------------------
def cmd_live():
    """Homepage se live/recent matches."""
    print(c("bold", "\n  🏏 LIVE & RECENT MATCHES\n"))
    html = fetch(BASE + "/")
    data = rsc_data(html)
    mj = extract_json(data, '"matchesList"')
    if not mj:
        print(c("red", "  [-]" + " Matches data nahi mila — network/site issue?"))
        return 1
    obj = json.loads(mj)
    matches = obj.get("matches", [])
    if not matches:
        print(c("gold", "  [!]" + " Koi match nahi mila"))
        return 0
    print(c("dim", f"  {len(matches)} match(es)\n"))
    for match in matches:
        s = get_match_summary(match)
        state_ico = {"live": "🔴", "preview": "⏳", "complete": "✅"}.get(
            (s["state"] or "").lower(), "•")
        print(f"  {state_ico} [{c('cyan', str(s['id']))}] "
              f"{c('bold', s['t1'])} {s['s1']} vs "
              f"{c('bold', s['t2'])} {s['s2']}")
        print(c("dim", f"     {s['series']} · {s['desc']} · {s['format']}"))
        print(c("dim", f"     {s['status']}"))
        print()
    print(c("dim", "  Scorecard:  zyrox-cric.py scorecard <matchId>"))
    print(c("dim", "  Summary:    zyrox-cric.py summary <matchId>"))
    print(c("dim", "  Live watch: zyrox-cric.py watch <matchId>"))
    return 0


def find_slug(match_id):
    """matchId -> scorecard page slug (homepage matchesList se)."""
    try:
        html = fetch(BASE + "/")
        data = rsc_data(html)
        mj = extract_json(data, '"matchesList"')
        if not mj:
            return None
        for match in json.loads(mj).get("matches", []):
            mi = match.get("match", {}).get("matchInfo", {})
            if str(mi.get("matchId")) == str(match_id):
                t1 = mi.get("team1", {}).get("teamSName", "").lower()
                t2 = mi.get("team2", {}).get("teamSName", "").lower()
                sname = re.sub(r"[^a-z0-9]+", "-", (mi.get("seriesName", "") or "").lower()).strip("-")
                desc = re.sub(r"[^a-z0-9]+", "-", (mi.get("matchDesc", "") or "").lower()).strip("-")
                return f"{t1}-vs-{t2}-{desc}-{sname}"[:120]
    except Exception:
        pass
    return None


def cmd_scorecard(match_id):
    """Full scorecard: batting + bowling, innings-wise."""
    slug = find_slug(match_id)
    if not slug:
        print(c("red", "  [-] Match slug nahi mila (homepage se) — match id sahi hai?"))
        return 1
    url = f"{BASE}/live-cricket-scorecard/{match_id}/{slug}"
    html = fetch(url)
    data = rsc_data(html)
    sj = extract_json(data, '"scoreCard"')
    if not sj:
        print(c("red", "  [-] Scorecard data nahi mila"))
        return 1
    innings = json.loads(sj)
    print(c("bold", f"\n  📋 SCORECARD — {match_id}\n"))
    for inn in innings:
        bt = inn.get("batTeamDetails", {})
        bd = bt.get("batsmenData", {})
        sd = inn.get("scoreDetails", {})
        r = sd.get("runs", "?")
        w = sd.get("wickets", "?")
        ov = sd.get("overs", "?")
        rr = sd.get("runRate", "")
        ext = inn.get("extrasData", {})
        ext_txt = ""
        if ext:
            ext_txt = f"  ·  Extras: {ext.get('total', 0)} (b {ext.get('byes', 0)}, lb {ext.get('legByes', 0)}, wd {ext.get('wides', 0)}, nb {ext.get('noBalls', 0)})"
        print(c("cyan", f"  ▓ {bt.get('batTeamName', '?')}  {r}/{w} ({ov}ov)"
                        f"{('  RR ' + str(rr)) if rr else ''}"))
        if ext_txt:
            print(c("dim", ext_txt))
        print(c("dim", "  ───────────────────────────────────────────────"))
        print(c("dim", f"  {'Batter':<22}{'R':>4}{'B':>5}{'4s':>4}{'6s':>4}{'SR':>7}"))
        for k, b in sorted(bd.items(), key=lambda kv: kv[0]):
            if not b.get("batName"):
                continue
            name = b["batName"]
            out = b.get("outDesc", "")
            line = f"  {name[:21]:<22}{b.get('runs', 0):>4}{b.get('balls', 0):>5}" \
                   f"{b.get('fours', 0):>4}{b.get('sixes', 0):>4}{b.get('strikeRate', ''):>7}"
            print(line)
            if out and out != "not out":
                print(c("dim", f"     └ {out}"))
            else:
                print(c("green", f"     └ {out}"))
        # bowlers
        bwt = inn.get("bowlTeamDetails", {})
        bw = bwt.get("bowlersData", {})
        if bw:
            print(c("dim", f"  {'Bowler':<22}{'O':>5}{'M':>4}{'R':>5}{'W':>4}{'Econ':>7}"))
            for k, b in sorted(bw.items(), key=lambda kv: kv[0]):
                if not b.get("bowlName"):
                    continue
                # NOTE: API ka 'maidens' field actually dots count karta hai
                print(f"  {b['bowlName'][:21]:<22}{b.get('overs', 0):>5}{b.get('dots', 0):>4}"
                      f"{b.get('runs', 0):>5}{b.get('wickets', 0):>4}{b.get('economy', ''):>7}")
        print()
    return 0


def cmd_summary(match_id):
    """Match summary — homepage se match info."""
    html = fetch(BASE + "/")
    data = rsc_data(html)
    mj = extract_json(data, '"matchesList"')
    if not mj:
        print(c("red", "  [-] Data nahi mila"))
        return 1
    for match in json.loads(mj).get("matches", []):
        s = get_match_summary(match)
        if str(s["id"]) == str(match_id):
            print(c("bold", f"\n  🏏 MATCH — {s['t1']} vs {s['t2']}"))
            print(f"  {c('cyan', s['t1'])}  {c('bold', s['s1'])}")
            print(f"  {c('cyan', s['t2'])}  {c('bold', s['s2'])}")
            print(c("dim", f"  Status:   {s['status']}"))
            print(c("dim", f"  Series:   {s['series']} ({s['desc']}, {s['format']})"))
            print(c("dim", f"  Venue:    {s['venue']}"))
            print(c("dim", f"  Start:    {s['start']}"))
            print(c("dim", "  Scorecard:  zyrox-cric.py scorecard " + str(match_id)))
            return 0
    print(c("red", "  [-] Match nahi mila"))
    return 1


def cmd_watch(match_id, interval=20):
    """Live score ticker — auto-refresh summary."""
    print(c("bold", f"\n  👁 WATCH — match {match_id} (refresh {interval}s, Ctrl+C stop)\n"))
    last = ""
    try:
        while True:
            html = fetch(BASE + "/")
            data = rsc_data(html)
            mj = extract_json(data, '"matchesList"')
            found = False
            if mj:
                for match in json.loads(mj).get("matches", []):
                    s = get_match_summary(match)
                    if str(s["id"]) == str(match_id):
                        found = True
                        line = f"  {s['t1']} {s['s1']} vs {s['t2']} {s['s2']} — {s['status']}"
                        now = datetime.now().strftime("%H:%M:%S")
                        print(c("cyan", f"  [{now}] ") + c("bold", line))
                        if line != last:
                            last = line
            if not found:
                print(c("gold", f"  [{datetime.now().strftime('%H:%M:%S')}] Match nahi mila — live/recent list me nahi hai?"))
            time.sleep(interval)
    except KeyboardInterrupt:
        print(c("dim", "\n  watch band."))
    return 0


# ----------------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------------
def usage():
    print(c("bold", "\n  ZYROX CRICBUZZ — Live cricket scores CLI"))
    print(c("dim", "  reverse-engineered from cricbuzz.com (RSC payload)\n"))
    print("  USAGE:")
    print("    zyrox-cric.py live                  live/recent matches + scores")
    print("    zyrox-cric.py scorecard <matchId>   full scorecard (batting+bowling)")
    print("    zyrox-cric.py summary <matchId>     match summary")
    print("    zyrox-cric.py watch <matchId>       auto-refresh score ticker")
    print("    zyrox-cric.py search <query>        match/series search")
    print("    zyrox-cric.py help                  ye help\n")
    print(c("dim", "  Example:  zyrox-cric.py scorecard 144959\n"))


def cmd_search(query):
    """Homepage matches me query filter (team/series) — CricBuzz ka search page ab nahi hai."""
    q = query.lower()
    html = fetch(BASE + "/")
    data = rsc_data(html)
    mj = extract_json(data, '"matchesList"')
    if not mj:
        print(c("red", "  [-] Data nahi mila"))
        return 1
    results = []
    for match in json.loads(mj).get("matches", []):
        s = get_match_summary(match)
        hay = f"{s['t1']} {s['t2']} {s['series']} {s['desc']} {s['status']}".lower()
        if q in hay:
            results.append(s)
    print(c("bold", f"\n  🔎 '{query}' — {len(results)} match(es)\n"))
    for s in results:
        print(f"  [{c('cyan', str(s['id']))}] {s['t1']} {s['s1']} vs {s['t2']} {s['s2']}")
        print(c("dim", f"     {s['series']} · {s['status']}\n"))
    if not results:
        print(c("gold", "  [!] Koi match nahi mila — team code (e.g. IND, AUS) ya series naam try karo"))
    return 0


def main():
    global NO_COLOR
    if "--no-color" in sys.argv:
        NO_COLOR = True
        sys.argv.remove("--no-color")
    args = sys.argv[1:]
    if not args or args[0] in ("help", "-h", "--help"):
        usage()
        return 0
    cmd = args[0]
    try:
        if cmd == "live":
            return cmd_live()
        if cmd in ("scorecard", "sc"):
            if len(args) < 2:
                print(c("red", "  usage: zyrox-cric.py scorecard <matchId>"))
                return 1
            return cmd_scorecard(args[1])
        if cmd in ("summary", "info"):
            if len(args) < 2:
                print(c("red", "  usage: zyrox-cric.py summary <matchId>"))
                return 1
            return cmd_summary(args[1])
        if cmd == "watch":
            if len(args) < 2:
                print(c("red", "  usage: zyrox-cric.py watch <matchId>"))
                return 1
            interval = int(args[2]) if len(args) > 2 and args[2].isdigit() else 20
            return cmd_watch(args[1], interval)
        if cmd == "search":
            if len(args) < 2:
                print(c("red", "  usage: zyrox-cric.py search <query>"))
                return 1
            return cmd_search(" ".join(args[1:]))
        usage()
        return 0
    except KeyboardInterrupt:
        print()
        return 0
    except urllib.error.URLError as e:
        print(c("red", f"  [-] Network error: {e.reason} — internet check karo"))
        return 1
    except Exception as e:
        print(c("red", f"  [-] Error: {e}"))
        return 1


if __name__ == "__main__":
    sys.exit(main())
