# SCOUT C2 — EDTH Munich 2026

**Challenges:** 01-ats (3D Graph Exploration & Surveillance) + 01-se3 Track 2 (Tactical Change Detection)  
**Demo:** Tactical command system for 5 autonomous agents (1 PiCrawler + 4 simulated) with a 2D village map, FOV coverage, threat/change alerts, an admin dashboard, and a field-operator mobile web app.

---

## The Pitch in One Line

A €200 autonomous ground sensor node connected to a military-style C2 interface: one map, every agent, complete situational awareness.

---

## Project Layout

```
edth-munich-2026/
├── challenge/graph_explo/               # Cloned 01-ats evaluation repo
├── side-quests/01-se3-change-detection/ # 01-se3 Track 2 submission
├── src/
│   ├── algorithm/
│   │   └── explorer.py                  # 01-ats submission
│   ├── robot/
│   │   ├── crawler.py                   # PiCrawler wrapper
│   │   ├── camera.py                    # Camera wrappers
│   │   └── demo_loop.py                 # Physical robot state machine
│   └── c2/
│       ├── server.py                    # Flask telemetry/video/command server
│       ├── simulator.py                 # 2D tactical map simulator
│       └── video_renderer.py            # 3-minute demo video generator
├── src/admin/index.html                 # Admin dashboard (tablet/laptop)
├── src/operator/index.html              # Field operator app (phone)
├── config/params.toml                   # Demo parameters
├── tests/test_algorithm.py              # Explorer unit tests
├── docs/
│   ├── IMPLEMENTATION_PLAN.md           # Weekend build plan
│   ├── PITCH.md                         # Pitch script
│   ├── DEMO_SCRIPT.md                   # 3-minute demo flow
│   └── HARDWARE_CHECKLIST.md            # What to bring
└── scripts/setup_pi.sh                  # Pi setup helpers
```

---

## Quick Start

### 1. Evaluate 01-ats

```bash
cd challenge/graph_explo
uv run run_eval.py --submission ../../src/algorithm/explorer.py --graphs graphs/train --quiet
```

### 2. Evaluate 01-se3 Track 2

```bash
cd side-quests/01-se3-change-detection
python change_detector.py before.jpg after.jpg output.jpg
```

### 3. Run the simulator / video preview

```bash
python src/c2/simulator.py
```

### 4. Render the 3-minute demo video

```bash
python src/c2/video_renderer.py
```

### 5. Run the telemetry server

```bash
# Install C2 deps once
pip install -r requirements.txt

python src/c2/server.py
```

Then open:
- Admin dashboard: `http://<laptop-ip>:5050/admin`
- Operator app: `http://<laptop-ip>:5050/operator`

### 6. Run the robot demo (on the Pi)

```bash
python src/robot/demo_loop.py
```

---

## Current Status

- [x] Official 01-ats challenge repo cloned (`SamEberl/graph_explo`)
- [x] Explorer algorithm skeleton
- [x] Change-detection side quest skeleton
- [x] Flask telemetry / command server (`src/c2/server.py`)
- [x] 2D tactical simulator with 5 agents, FOV, coverage, alerts
- [x] Admin dashboard frontend (`src/admin/index.html`)
- [x] Field operator mobile frontend (`src/operator/index.html`)
- [ ] Algorithm tuned on training graphs
- [ ] Robot integration tested
- [ ] 3-minute demo video rendered
- [ ] Pitch rehearsed

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
