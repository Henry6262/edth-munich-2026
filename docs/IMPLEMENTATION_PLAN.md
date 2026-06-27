# SCOUT C2 — Implementation Plan

> Weekend build plan for EDTH Munich 2026.  
> Updated after the research-agent conversation in `/Users/henry/Downloads/Kimi_Agent_机器人防御挑战 (1)`.

---

## 1. The Goal (One Sentence)

Ship a working C2 demo with a 2D tactical map, an admin dashboard, a mobile operator app, a live PiCrawler robot as Agent 1, and both challenge submissions (01-ats + 01-se3 Track 2) by Sunday demo time.

---

## 2. The Demo in 3 Minutes

1. **The Drop** — 5 agents spawn on a 2D village map.
2. **The Sweep** — FOV cones reveal green coverage; fog-of-war dissolves.
3. **The Threat** — Agent 3 stops; red alert: "THREAT — Building 7."
4. **The Response** — Admin clicks DEPLOY; cut to live robot walking the tape path; phone shows camera feed with red-card detection.
5. **The Recon** — "2 hours later"; agents sweep again; yellow alert: "CHANGE — Door closed → open."
6. **The Big Picture** — 80% coverage, all agents, all alerts, mobile app shown.
7. **The Close** — "SCOUT C2. One map. Every agent. Complete situational awareness."

---

## 3. Architecture

```
LAPTOP (dev machine)
├── src/c2/simulator.py        # 2D map, agents, FOV, coverage
├── src/c2/video_renderer.py   # 3-minute MP4 compositor
├── src/c2/server.py           # Flask: /api/state, /api/command, /video_feed
├── src/admin/index.html       # Admin dashboard (React/Vite or plain HTML)
└── src/operator/index.html    # Mobile operator app (single HTML file)

PI 5 (inside PiCrawler)
├── src/robot/crawler.py       # Movement wrapper
├── src/robot/camera.py        # IMX500 / Pi camera
└── src/robot/demo_loop.py     # Patrol → detect → track → report

SUBMISSIONS
├── src/algorithm/explorer.py                         # 01-ats
└── side-quests/01-se3-change-detection/change_detector.py  # 01-se3 Track 2
```

---

## 4. Data Contract (JSON)

`GET /api/state` returns:

```json
{
  "mission_time": "14:32:07",
  "sector": "Sector 7",
  "coverage_pct": 67,
  "agents": [
    {
      "id": "A-1",
      "name": "ALPHA",
      "type": "GROUND",
      "color": "#00FF88",
      "status": "PATROLLING",
      "battery": 78,
      "signal": 92,
      "position": {"x": 120, "y": 340, "angle": 225},
      "fov": {"range": 80, "angle": 90}
    }
  ],
  "alerts": [
    {"type": "THREAT", "agent": "A-3", "location": "Building 7", "confidence": 0.91, "time": "14:35:22"},
    {"type": "CHANGE", "agent": "A-4", "location": "Building 3", "detail": "Door CLOSED → OPEN", "time": "14:47:33"}
  ],
  "mission_log": [
    {"time": "14:35:22", "type": "THREAT", "text": "A-3 THREAT — Building 7"}
  ],
  "change_log": [
    {"time": "14:47:33", "agent": "A-4", "text": "Door OPEN (was CLOSED)"}
  ]
}
```

`POST /api/command` accepts:

```json
{"command": "DEPLOY" | "HOLD" | "RECON" | "RECALL" | "MARK", "agent": "A-3"}
```

---

## 5. Tonight's Focus (Front End + Telemetry Skeleton)

**Goal:** Open the admin dashboard on a laptop and the operator app on a phone and see a shared, animated tactical picture — without the robot plugged in.

### 5.1 Back end

- [ ] Create `src/c2/server.py` with Flask.
  - `GET /api/state` — returns simulated mission state.
  - `POST /api/command` — accepts commands, updates simulated state.
  - `GET /video_feed` — MJPEG stream (placeholder loop for now).
  - `GET /admin` / `/operator` — serve the static frontends.
- [ ] Create `src/c2/simulator.py`.
  - Procedural village: 10 buildings, roads, drop zone.
  - 5 agents with pre-planned waypoints.
  - FOV cone geometry and coverage polygon union.
  - Trigger threat at Building 7 and change at Building 3 after set times.
  - Advance state every 200 ms.

### 5.2 Admin dashboard (`src/admin/index.html`)

- [ ] Top bar: SCOUT C2 logo, sector, live clock, online status.
- [ ] Main tactical map (Canvas):
  - Buildings, roads, fog-of-war, green coverage overlay.
  - 5 agent icons with directional arrows and pulsing rings.
  - FOV cones, threat/change markers.
- [ ] Right panel:
  - Squad status mini cards.
  - Coverage progress bar.
  - Active alerts list.
  - Command actions: DEPLOY, RECON, RECALL.
- [ ] Bottom feeds panel:
  - Live camera feed, map zoom, simulated thermal, telemetry.
- [ ] Bottom logs:
  - Mission log and change-detection log.
- [ ] Poll `/api/state` every 500 ms; send commands via `/api/command`.

### 5.3 Operator app (`src/operator/index.html`)

- [ ] Screen 1 — Splash / Mission Select: Clear & Hold, Engage & Clear, Recon Sweep.
- [ ] Screen 2 — Squad Dashboard:
  - Minimap, 5 agent cards, coverage bar, quick actions, active alerts.
- [ ] Screen 3 — Agent Detail / Live Feed:
  - Live feed placeholder, status bars, detection panel, controls (DEPLOY, HOLD, MARK, DETONATE with double-tap confirm).
- [ ] Screen 4 — Threat Alert (full-screen modal).
- [ ] Screen 5 — Change Detection (before/after images).
- [ ] Screen 6 — Mission Log.
- [ ] Poll `/api/state` every 500 ms; commands via `/api/command`.

### 5.4 Shared UI kit

- Put common CSS variables, colors, and helper JS in a single file or inline.
- Colors from `DESIGN_SYSTEM_AND_SCREENS.md`:
  - BG_PRIMARY `#0A0E1A`, BG_PANEL `#0F1629`, BG_ELEVATED `#141D35`
  - ACCENT_CYAN `#00F0FF`, ACCENT_RED `#FF3366`, ACCENT_YELLOW `#FFCC00`, ACCENT_GREEN `#00FF88`
- Fonts: Rajdhani / Orbitron for headlines, Inter for body, JetBrains Mono for data.
- Minimum touch target 64 px for operator buttons.

### 5.5 Success Criteria for Tonight

- [ ] `python src/c2/server.py` starts without errors.
- [ ] Admin dashboard shows animated 2D map with 5 moving agents and growing green coverage.
- [ ] Operator app shows the squad dashboard and receives state updates.
- [ ] Clicking DEPLOY / RECON / RECALL in either UI updates the shared state.
- [ ] Threat alert appears automatically at the scripted time and opens the threat modal on the operator app.

---

## 6. Tomorrow Morning — Simulation + Video

**Goal:** Turn the simulator into a cinematic 3-minute video and integrate real agent paths from `explorer.py`.

- [ ] Generate 5 exploration routes using `src/algorithm/explorer.py` on a challenge graph.
- [ ] Convert graph waypoints into 2D map waypoints.
- [ ] Refine FOV cone rendering and coverage polygon union.
- [ ] Add scene scripting to `src/c2/video_renderer.py`:
  - Scene 1: Drop (0:00-0:15)
  - Scene 2: Sweep (0:15-0:45)
  - Scene 3: Threat (0:45-1:15)
  - Scene 4: Response / robot deploy (1:15-1:45)
  - Scene 5: Recon / change detection (1:45-2:15)
  - Scene 6: Big picture (2:15-2:45)
  - Scene 7: Close (2:45-3:00)
- [ ] Add admin panel overlay to video frames.
- [ ] Render a 30-second test MP4 first, then full 3-minute MP4.
- [ ] Run 01-ats evaluator and tune `explorer.py` if score drops.

---

## 7. Tomorrow Afternoon — Robot + Change Detection Integration

**Goal:** Physical robot walks as Agent 1 and the system detects red/blue/yellow cards.

- [ ] Write `src/robot/demo_loop.py` state machine:
  - PATROL → walk tape path
  - DETECTED → stop, turn toward object
  - TRACKING → keep object centered
  - REPORTING → send detection to Flask server
- [ ] Integrate IMX500 / OpenCV detection in `src/robot/camera.py`.
- [ ] Classify red card = THREAT, blue/yellow = CIVILIAN/MARKER.
- [ ] Make `src/c2/server.py` accept real robot telemetry and camera feed instead of simulation when a robot is connected.
- [ ] Capture before/after sector photos for change detection.
- [ ] Run `change_detector.py` on pairs and feed results into `/api/state`.
- [ ] Practice the 3-minute pitch with video + live robot + app transitions.

---

## 8. Sunday — Demo Day

- [ ] 09:00 — Set up table, tape path, boxes, robot, laptop, phone.
- [ ] 10:00 — Dress rehearsal ×3.
- [ ] 11:00 — Submit `explorer.py` and `change_detector.py` if not already done.
- [ ] 11:30 — Record backup video in case live robot fails.
- [ ] 12:00 — Final mental prep.
- [ ] 13:00 — Demo.

---

## 9. Risks & Mitigations

| Risk | Mitigation |
|---|---|
| Robot falls off table | Large table, edge detection, practice |
| IMX500 doesn't detect cards in venue light | High-contrast cards, fallback color detection |
| Wi-Fi flake | Run server on localhost + phone hotspot, have offline mode |
| Video render too slow | Render overnight, keep 30 s test as backup |
| UI too complex for 42 h | Operator app is one HTML file; admin uses Canvas, no WebGL |
| Servo failure | Bring spare servos, calibrate Friday night |

---

## 10. Key Reference Files

- Full research conversation: `/Users/henry/Downloads/Kimi_Agent_机器人防御挑战 (1)/`
- UI design spec: `/Users/henry/Downloads/Kimi_Agent_机器人防御挑战 (1)/DESIGN_SYSTEM_AND_SCREENS.md`
- Master plan: `/Users/henry/Downloads/Kimi_Agent_机器人防御挑战 (1)/THE_PLAN.md`
- C2 concept: `/Users/henry/Downloads/Kimi_Agent_机器人防御挑战 (1)/C2_TACTICAL_COMMAND_SYSTEM.md`

---

*Focus tonight: telemetry server + admin dashboard + operator app. Everything else is tomorrow.*
