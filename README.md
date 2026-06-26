# SCOUT — EDTH Munich 2026

**Challenge:** 01-ats — 3D Graph Exploration & Surveillance  
**Team:** Henry + recruited teammates  
**Hardware:** PiCrawler quadruped + Raspberry Pi 5 + Sony IMX500 AI Camera

## The Pitch in One Line

A €200 autonomous ground sensor node that walks a perimeter, explores an unknown graph, and surveils it — submitted as a Python solution to the ATS GmbH challenge and demonstrated live with a walking robot.

## Project Layout

```
edth-munich-2026/
├── challenge/graph_explo/   # Cloned 01-ats evaluation repo
├── src/
│   ├── algorithm/           # Challenge Explorer policy
│   │   └── explorer.py      # Our submission-ready Explorer class
│   ├── robot/               # PiCrawler + camera control
│   │   ├── crawler.py
│   │   └── camera.py
│   ├── dashboard/           # Streamlit tactical UI
│   │   └── app.py
│   └── main.py              # Physical demo orchestration
├── config/
│   └── params.toml          # Robot demo parameters
├── tests/
│   └── test_algorithm.py    # Unit tests for Explorer
├── docs/
│   ├── PITCH.md             # Word-for-word pitch script
│   └── DEMO_SCRIPT.md       # 3-minute demo flow
└── scripts/
    └── setup_pi.sh          # Pi setup helpers
```

## Quick Start

### 1. Run the challenge evaluation

```bash
cd challenge/graph_explo
uv run run_eval.py --submission ../../src/algorithm/explorer.py --graphs graphs/train --quiet
```

### 2. Run the robot demo (on the Pi)

```bash
python src/main.py
```

### 3. Run the dashboard

```bash
streamlit run src/dashboard/app.py
```

## Current Status

- [x] Challenge repo cloned
- [x] Explorer algorithm skeleton
- [ ] Algorithm tuned on training graphs
- [ ] Robot integration tested
- [ ] Dashboard complete
- [ ] Pitch rehearsed

## Hardware Checklist for Venue

- [ ] PiCrawler robot
- [ ] Raspberry Pi 5 + official 27W PSU
- [ ] Sony IMX500 AI Camera
- [ ] Standard Pi Camera (wide)
- [ ] USB robot-arm / robot-eyes camera
- [ ] microSD card + reader (buy at venue if missing)
- [ ] Ethernet cable (buy at venue if missing)
- [ ] Power bank
- [ ] Colored electrical tape (patrol path)
- [ ] Cardboard boxes (3 sectors)
- [ ] "Drone" cutout (black cardboard on stick)
- [ ] Laptop

## What NOT to Build

- Mobile app with soldier shared state — out of scope for 42 hours
- Cloud backend — no internet dependency, demo must work offline
- Custom drone detection model — use MobileNet SSD out of the box
- Real SLAM — fake the map with the challenge graph / tape path
