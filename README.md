# SCOUT C2 — EDTH Munich 2026

SCOUT C2 is a hackathon prototype for commanding low-cost autonomous reconnaissance agents from one tactical interface. The demo combines a Flask telemetry server, a 2D admin dashboard, a Three.js 3D battlefield view, a mobile operator web app, a PiCrawler robot path, and two EDTH challenge submissions.

**Pitch:** a EUR 200 autonomous ground sensor node connected to a military-style C2 system: one map, every agent, complete situational awareness.

## Challenge Goals

### 01-ats — 3D Graph Exploration & Surveillance

**Sponsor:** Autonomous Teaming Solutions ATS GmbH

Goal: design an algorithm for an agent in an unknown 3D graph. The agent can only see nodes within sensor range and can only move along discovered edges.

The challenge has two phases:

1. **Explore:** observe enough of the unknown graph to reach the configured explore threshold.
2. **Surveil:** reuse the map and plan an efficient re-observation sweep to reach the configured surveillance threshold.

The score is total flight distance across both phases, so the policy must decide what to visit, what to skip, and how to avoid waste.

SCOUT maps this into the demo as live multi-agent exploration: agents sweep a village, FOV cones paint observed space, coverage grows, and the admin UI shows exploration and surveillance progress from `/api/state`.

### 01-se3 — Tactical Intelligence from Live 3D Battlefield Reconstruction

**Sponsor:** SE3 Labs

Goal: a 3D reconstruction of a battlefield contains answers operators need, but it needs an intelligence layer. The challenge supports tactical position intelligence, change detection, or a combined approach using SE3-provided data.

SCOUT uses the combined story:

- The 3D reconstruction becomes the tactical map layer.
- Agents and alerts are projected into that map in real time.
- A second-pass recon sweep triggers tactical change detection.
- Yellow change markers show what changed between patrol passes.

The current implementation includes the Track 2 change-detection submission in `side-quests/01-se3-change-detection/change_detector.py` and exposes SE3 demo status through `/api/state`.

## What We Built

- **Offline C2 server:** `src/c2/server.py` serves all dashboards, mission state, commands, video placeholder, and 3D assets.
- **Live simulator:** five agents move through a `4200 x 3200` tactical zone with A*-routed paths around buildings.
- **2D admin dashboard:** `src/admin/index.html` renders the real simulation coordinate system, FOV cones, coverage, buildings, roads, threats, changes, command actions, and challenge-goal status.
- **3D admin simulation map:** `frontend/src/components/TacticalMap3D.ts` renders the same mission in Three.js with buildings, roads, agents, trails, FOV cones, coverage, terrain, tree clusters, threat/change markers, and WASD camera movement.
- **Mobile operator app:** `src/operator/index.html` gives a phone-sized squad view, minimap, camera feed, alerts, and command buttons.
- **ATS submission:** `src/algorithm/explorer.py` contains the 01-ats graph exploration policy.
- **SE3 submission:** `side-quests/01-se3-change-detection/change_detector.py` contains an OpenCV-only tactical change detector.
- **Challenge telemetry:** `/api/state` now includes `challenge_goals.ats` and `challenge_goals.se3`, so the UI can show what has been achieved instead of only showing moving dots.
- **3D battlefield data:** `static/village.ply` and `side-quests/01-se3-change-detection/data/point_cloud_demo.ply` provide procedural / SE3-style reconstruction assets for the demo.

## Demo Routes

Run the server, then open:

- Admin 2D dashboard: `http://localhost:5050/admin`
- Admin 3D map: `http://localhost:5050/3d`
- Operator mobile app: `http://localhost:5050/operator`
- Mission JSON: `http://localhost:5050/api/state`
- Village point cloud: `http://localhost:5050/village.ply`
- SE3 point cloud demo: `http://localhost:5050/point_cloud.ply`

## Quick Start

```bash
pip install -r requirements.txt
npm --prefix frontend install
npm --prefix frontend run build
python src/c2/server.py
```

For frontend-only Three.js development:

```bash
npm --prefix frontend run dev
```

For the physical robot demo on the Pi:

```bash
python src/robot/demo_loop.py
```

## Challenge Commands

Evaluate 01-ats:

```bash
cd challenge/graph_explo
uv run run_eval.py --submission ../../src/algorithm/explorer.py --graphs graphs/train --quiet
```

Run 01-se3 change detection:

```bash
cd side-quests/01-se3-change-detection
python change_detector.py before.jpg after.jpg output.jpg
```

Generate the procedural village point cloud:

```bash
python src/video/generate_village.py
```

Render the 3-minute demo video:

```bash
python src/c2/video_renderer.py
```

## `/api/state` Contract

The dashboards poll `GET /api/state` every 500 ms. The response includes:

- Mission time, mode, sector, and coverage percentage.
- Five agents with id, type, status, battery, signal, position, angle, color, and FOV.
- Building footprints and road polylines shared by both 2D and 3D maps.
- Active threat/change alerts.
- Mission log and change log.
- `challenge_goals.ats`: explore/surveil thresholds, progress, phase, and achievement status.
- `challenge_goals.se3`: 3D intelligence status, point-cloud source, detected changes, and achievement status.

Commands go through `POST /api/command`:

```json
{"command": "DEPLOY", "agent": "A-3"}
```

Supported commands: `DEPLOY`, `HOLD`, `RECON`, `RECALL`, `MARK`.

## Project Layout

```text
edth-munich-2026/
├── challenge/graph_explo/               # External 01-ats evaluator repo
├── frontend/                            # React + Vite + Three.js 3D admin map
│   └── src/components/TacticalMap3D.ts   # Main 3D battlefield runtime
├── side-quests/01-se3-change-detection/ # 01-se3 Track 2 submission
├── src/
│   ├── admin/index.html                 # 2D admin dashboard
│   ├── algorithm/explorer.py            # 01-ats submission
│   ├── c2/server.py                     # Flask telemetry/video/command server
│   ├── operator/index.html              # Mobile operator web app
│   ├── robot/                           # PiCrawler + camera wrappers
│   └── video/                           # Point-cloud generation
├── static/village.ply                   # Generated 3D village point cloud
└── docs/                                # Pitch, demo plan, hardware checklist
```

## Current Status

- [x] 01-ats challenge repo integrated locally.
- [x] 01-ats explorer submission file exists.
- [x] 01-se3 tactical change detector exists.
- [x] Flask C2 server serves `/admin`, `/3d`, `/operator`, `/api/state`, `/api/command`, `/video_feed`, and point-cloud assets.
- [x] 2D admin dashboard works on live simulator state.
- [x] 3D admin map works on live simulator state.
- [x] 3D flickering floor replaced with stable matte terrain.
- [x] Terrain patches and tree clusters added around the 3D tactical zone.
- [x] 3D markers show threat/change alerts on buildings.
- [x] Challenge-goal telemetry added to backend and admin surfaces.
- [x] Operator mobile web app polls the same state and sends commands.
- [ ] Run and tune the 01-ats evaluator on training graphs.
- [ ] Capture real before/after frames for SE3 change detection.
- [ ] Test PiCrawler integration as Agent 1.
- [ ] Record the final 3-minute pitch video.

---

## Hardware Checklist for Venue

- [ ] PiCrawler robot
- [ ] Raspberry Pi 5 + official 27W PSU
- [ ] Sony IMX500 AI Camera
- [ ] Standard Pi Camera (wide)
- [ ] USB robot-arm / robot-eyes camera
- [ ] microSD card + reader
- [ ] Ethernet cable
- [ ] Power bank
- [ ] Colored electrical tape (patrol path)
- [ ] Cardboard boxes (3 sectors / buildings)
- [ ] Red / blue / yellow cards (threat / civilian / change markers)
- [ ] "Drone" cutout (black cardboard on stick)
- [ ] Laptop
- [ ] Phone for operator app

---

## What NOT to Build

- Native mobile app — browser page is enough
- Cloud backend — demo must work offline
- Custom drone / threat detection model — use MobileNet SSD / IMX500 out of the box
- Real SLAM — fake the map with the challenge graph / tape path
- LoRa / ATAK integration — mention in pitch only
- Explosive payload mechanism — never demo at a hackathon
