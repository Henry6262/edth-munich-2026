# CLAUDE.md — EDTH Munich 2026 / SCOUT C2

> Project-specific agent instructions. Read this before touching code.

---

## What this project is

Hackathon submission for **EDTH Munich 2026**:

- **01-ats** (ATS GmbH) — 3D Graph Exploration & Surveillance → `src/algorithm/explorer.py`
- **01-se3 Track 2** (SE3 Labs) — tactical change detection → `side-quests/01-se3-change-detection/change_detector.py`

Live demo: **SCOUT C2**, a tactical command system where 5 autonomous agents (4 simulated + 1 PiCrawler robot) explore a 2D village, their camera FOV paints cleared areas green, threats show red, changes show yellow, and a field operator sees everything on a mobile "minimap on steroids."

**External challenge assets:**
- 01-ats evaluator: cloned from `https://github.com/SamEberl/graph_explo` into `challenge/graph_explo/` (do not commit this folder to our repo).
- 01-se3 data: provided by SE3 Labs at the event; contact Alexander Hobmeier. Place assets in `side-quests/01-se3-change-detection/data/`.

---

## Tech stack

- Challenge eval: `uv` + `networkx`
- Algorithm / simulation / video: Python 3.10+, `matplotlib`, `numpy`, `shapely`, `opencv-python`
- Robot: `picrawler` SunFounder library + `picamera2` + OpenCV
- Telemetry & video server: Python `Flask` (runs on laptop)
- Admin dashboard: static web app (HTML/CSS/JS), served by Flask
- Field operator app: mobile web app, single HTML file, no build step
- Change detection: OpenCV (`side-quests/01-se3-change-detection/`)

---

## Key files

| File | Purpose |
|------|---------|
| `src/algorithm/explorer.py` | 01-ats submission. `Explorer` class. |
| `side-quests/01-se3-change-detection/change_detector.py` | 01-se3 Track 2 submission. |
| `src/c2/server.py` | Flask telemetry / video / command server. |
| `src/c2/simulator.py` | 2D tactical map simulator: agents, FOV, coverage, alerts. |
| `src/c2/video_renderer.py` | Composes matplotlib frames into the 3-minute demo MP4. |
| `src/robot/crawler.py` | PiCrawler movement wrapper. |
| `src/robot/camera.py` | Pi AI Camera + standard cam wrappers. |
| `src/robot/demo_loop.py` | Physical robot state machine (patrol → detect → track → report). |
| `src/admin/index.html` | Admin dashboard frontend. |
| `src/admin/3d.html` | Three.js 3D tactical view. |
| `src/video/generate_village.py` | Procedural village point cloud generator. |
| `static/village.ply` | Generated village point cloud (served by Flask). |
| `src/operator/index.html` | Field operator mobile frontend. |
| `docs/IMPLEMENTATION_PLAN.md` | This weekend's build plan. |
| `docs/PITCH.md` | Pitch script. |
| `docs/DEMO_SCRIPT.md` | Demo flow. |

---

## How to run things

```bash
# Evaluate 01-ats
cd challenge/graph_explo
uv run run_eval.py --submission ../../src/algorithm/explorer.py --graphs graphs/train --quiet

# Evaluate 01-se3 Track 2
cd side-quests/01-se3-change-detection
python change_detector.py before.jpg after.jpg output.jpg

# Generate procedural village point cloud
python src/video/generate_village.py

# Simulator / video preview
python src/c2/simulator.py

# Render 3-minute demo video
python src/c2/video_renderer.py

# Telemetry server (laptop) — runs on http://0.0.0.0:5050
python src/c2/server.py

# Robot demo loop (on Pi)
python src/robot/demo_loop.py

# Admin dashboard: http://<laptop-ip>:5050/admin
# 3D tactical view: http://<laptop-ip>:5050/3d
# Operator app: http://<laptop-ip>:5050/operator
```

---

## Constraints

- `src/algorithm/explorer.py` must be **one Python file** using only stdlib + `networkx`.
- `side-quests/01-se3-change-detection/change_detector.py` must be **one Python file**, OpenCV-only.
- Robot code must run on Raspberry Pi 5.
- Demo must work **offline** — no cloud dependencies.
- All UIs must work on local Wi-Fi / hotspot; no app-store builds.

---

## Design decisions

- **2D tactical map** for the main admin dashboard and demo video — readable and cinematic.
- **3D tactical view** (`/3d`) using a procedural village point cloud for the "wow" factor and pitch video B-roll.
- **Pre-recorded 3-minute cinematic video** for the main pitch; live robot + apps provide the "this is real" moments.
- **5 agents**: Agent 1 = PiCrawler (real); Agents 2-5 = simulated on the map.
- **Mobile operator app is a web page**, not React Native. One HTML file, opens in any browser.
- **Change detection is a built side quest** and is integrated into the C2 narrative.
- **Use MobileNet SSD / IMX500 out of the box.** No custom model training in 42 hours.
- **No real SLAM.** Village is procedural / challenge graph; robot walks a tape path.

---

## What we're NOT building

| Not Building | Why Not |
|---|---|
| Real-time multi-agent coordination | 5 pre-planned routes are enough |
| React Native / native mobile apps | Browser page is identical for demo, 10× faster |
| LoRa mesh / ATAK integration | Mention in pitch; build post-hackathon |
| Cloud backend or persistent database | Offline requirement |
| Custom threat-classification model | MobileNet SSD + color heuristics only |
| Real SLAM / 3D mapping | Procedural 3D village point cloud is good enough; no real-time SLAM |
| Explosive payload mechanism | Never demo explosives at a hackathon |

---

## Last updated

2026-06-27
