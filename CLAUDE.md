# CLAUDE.md — EDTH Munich 2026 / SCOUT

> Project-specific agent instructions. Read this before touching code.

## What this project is

Hackathon submission for **EDTH Munich 2026, Challenge 01-ats** (3D Graph Exploration & Surveillance by ATS GmbH). We also pitch it as a Counter-UAS / autonomous ground sensor node demo.

## Tech stack

- Python 3.10+
- Challenge eval: `uv` + `networkx`
- Robot: `picrawler` SunFounder library + `picamera2` + OpenCV
- Dashboard: Streamlit

## Key files

| File | Purpose |
|------|---------|
| `src/algorithm/explorer.py` | Challenge submission. Implements `Explorer` class. |
| `src/robot/crawler.py` | PiCrawler movement wrapper. |
| `src/robot/camera.py` | Pi AI Camera + standard cam wrappers. |
| `src/dashboard/app.py` | Streamlit tactical dashboard. |
| `src/main.py` | Physical demo loop (patrol → detect → track → report). |
| `challenge/graph_explo/` | Cloned evaluation repo. Do not modify. |
| `docs/PITCH.md` | Pitch script. |
| `docs/DEMO_SCRIPT.md` | Demo flow. |

## How to run things

```bash
# Evaluate algorithm
cd challenge/graph_explo
uv run run_eval.py --submission ../../src/algorithm/explorer.py --graphs graphs/train --quiet

# Robot demo
python src/main.py

# Dashboard
streamlit run src/dashboard/app.py
```

## Constraints

- Submit **one Python file** for the challenge (`src/algorithm/explorer.py`).
- Only stdlib + `networkx` allowed in submission.
- Robot code must run on Raspberry Pi 5.
- Demo must work offline — no cloud dependencies.

## Design decisions

- **One challenge only:** 01-ats. Mention 01-se3 Track 2 (change detection) as natural extension, but do not build a second submission.
- **Mobile app / shared soldier state is OUT.** Pitch it as a future feature.
- **Use MobileNet SSD out of the box.** No custom model training in 42 hours.
- **Fake SLAM.** The challenge provides the graph; the robot walks a tape path.

## Last updated

2026-06-26
