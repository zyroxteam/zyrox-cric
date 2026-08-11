# 🏏 ZYROX CRICBUZZ — Live Cricket Scores CLI

**CricBuzz.com ka reverse-engineered live cricket tool** — matches, scorecards,
summaries aur live score ticker. **Zero dependencies** (sirf Python 3.8+) —
Termux, Linux, macOS, Windows sab pe chalta hai.

---

## ✨ Features

| Feature | Command | Status |
|---|---|---|
| 🏏 **Live & recent matches** + scores | `live` | ✅ |
| 📋 **Full scorecard** (batting + bowling, innings-wise) | `scorecard <id>` | ✅ |
| 📊 **Match summary** (teams, status, venue, series) | `summary <id>` | ✅ |
| 👁 **Live watch** — auto-refresh score ticker | `watch <id>` | ✅ |
| 🔎 **Search** — team/series filter | `search <query>` | ✅ |
| 🎨 Neon ANSI output | sab commands | ✅ |

## 🚀 Install

### Termux
```bash
pkg install -y python git
git clone https://github.com/zyroxteam/zyrox-cric.git
cd zyrox-cric
chmod +x zyrox-cric.py
./zyrox-cric.py live
```

### Linux / macOS
```bash
git clone https://github.com/zyroxteam/zyrox-cric.git
cd zyrox-cric && chmod +x zyrox-cric.py
python3 zyrox-cric.py live
```

### Windows (PowerShell)
```
git clone https://github.com/zyroxteam/zyrox-cric.git
cd zyrox-cric
python zyrox-cric.py live
```

## 🕹 Usage

```bash
./zyrox-cric.py live                          # live/recent matches
./zyrox-cric.py scorecard 144959              # full scorecard
./zyrox-cric.py summary 144959                # match summary
./zyrox-cric.py watch 144959                  # live score ticker (20s refresh)
./zyrox-cric.py watch 144959 10               # 10s refresh
./zyrox-cric.py search "hundred"              # filter by team/series
./zyrox-cric.py --no-color live               # bina colors (log files ke liye)
```

### Live demo output

```
$ ./zyrox-cric.py live

  🏏 LIVE & RECENT MATCHES

  6 match(es)

  ✅ [144959] TRE 158/5 (100ov) vs SOU 159/4 (97ov)
     The Hundred Men's Competition 2026 · 29th Match · HUN
     Southern Brave won by 6 wkts

  ✅ [151015] IRE 206/10 (46.3ov) vs AFG 207/7 (44.5ov)
     Afghanistan tour of Ireland, 2026 · 3rd ODI · ODI
     Afghanistan won by 3 wkts
  ...

$ ./zyrox-cric.py scorecard 144959

  📋 SCORECARD — 144959

  ▓ Trent Rockets  158/5 (10ov)  RR 1.58
  ·  Extras: 8 (b 0, lb 2, wd 6, nb 0)
  ───────────────────────────────────────────────
  Batter                   R    B  4s  6s     SR
  Ben Duckett             17   14   4   0 121.43
     └ c David Miller b Marcus Stoinis
  Finn Allen              23   12   1   2 191.67
     └ b Chris Jordan
  ...
```

## 🔬 Reverse Engineering Notes

- CricBuzz ab **Next.js App Router** use karta hai — purane `/api/html/...` aur
  `/api/match/{id}/scorecard` endpoints **dead** hain (404/empty)
- Data **server-rendered RSC payload** me aata hai:
  `__next_f.push([1,"..."])` streams — **double-escaped** JS strings
- Extraction recipe:
  1. Page HTML me se `__next_f.push([1,"..."])` streams nikaalo
  2. **Do baar** JS-string unescape karo (nested escaping)
  3. `"matchesList"` (homepage) / `"scoreCard"` (scorecard page) anchor se
     balanced JSON extract karo
  4. `json.loads` → data ready
- Homepage anchors: `matchesList` → `{matches:[{match:{matchInfo, matchScore}}]}`
- Scorecard page anchors: `scoreCard` → `[{matchId, inningsId, batTeamDetails{batsmenData},
  bowlTeamDetails{bowlersData}, scoreDetails, extrasData}]`
- Match URL pattern: `/live-cricket-scorecard/{id}/{slug}` (slug homepage se milta hai)
- BowlersData ka `maidens` field actually **dots** count karta hai (API quirk)
- Commentary page sirf **live** matches ke liye hoti hai (complete pe 404)

## ⚠️ Disclaimer

- Educational / personal use — CricBuzz ke data ka aaraam se istemal karo
- Bulk scraping / reselling nahi
- Site ka structure kabhi bhi change ho sakta hai — tab tool update karna padega

---

<p align="center">Built with ❤️ by ZYROX Team · reverse-engineered from cricbuzz.com</p>
