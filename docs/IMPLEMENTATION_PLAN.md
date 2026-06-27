# SCOUT C2 — Implementation Plan

> Weekend build plan for EDTH Munich 2026.  
> Updated after the research-agent conversation in `/Users/henry/Downloads/Kimi_Agent_机器人防御挑战 (1)`.

---

## 1. The Goal (One Sentence)

Ship a working C2 demo with 2D + 3D tactical maps, an admin dashboard, a mobile operator app, a live PiCrawler robot as Agent 1, and both challenge submissions (01-ats + 01-se3 Track 2) by Sunday demo time.

---

## 2. The Demo in 3 Minutes

1. **The Drop** — 5 agents spawn on a 2D village map; cut to the 3D tactical view of the same village.
2. **The Sweep** — FOV cones reveal green coverage; fog-of-war dissolves in both 2D admin and 3D views.
3. **The Threat** — Agent 3 stops; red alert: "THREAT — Building 7." 3D view pulses the building.
4. **The Response** — Admin clicks DEPLOY; cut to live robot walking the tape path; phone shows camera feed with red-card detection.
5. **The Recon** — "2 hours later"; agents sweep again; yellow alert: "CHANGE — Door closed → open."
6. **The Big Picture** — 80% coverage, all agents, all alerts, 3D village and mobile app shown side by side.
7. **The Close** — "SCOUT C2. One map. Every agent. Complete situational awareness."

---

## 3. Architecture

```
LAPTOP (dev machine)
├── src/c2/server.py              # Flask: /api/state, /api/command, /video_feed, /3d, /village.ply
├── src/admin/index.html          # Admin dashboard (2D Canvas tactical map)
├── src/admin/3d.html             # Three.js 3D tactical view
├── src/operator/index.html       # Mobile operator app (single HTML file)
├── src/video/generate_village.py # Procedural village point cloud generator
├── src/c2/video_renderer.py      # 3-minute MP4 compositor (2D + overlay)
└── static/village.ply            # Generated terrain (ground, roads, trees, rocks)

PI 5 (inside PiCrawler)
├── src/robot/crawler.py          # Movement wrapper
├── src/robot/camera.py           # IMX500 / Pi camera
└── src/robot/demo_loop.py        # Patrol → detect → track → report

SUBMISSIONS
├── src/algorithm/explorer.py                              # 01-ats
└── side-quests/01-se3-change-detection/change_detector.py # 01-se3 Track 2
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
  "buildings": [
    {"id": "B1", "x": 80, "y": 80, "w": 90, "h": 70}
  ],
  "roads": [
    [[50, 400], [950, 400]]
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

## 5. Current Build Status

**What's Done**
- Flask server (`src/c2/server.py`) running on port 5050.
- Simulated mission state with 5 agents, FOV cones, coverage union, scripted threat/change alerts.
- Agent routes use A* pathfinding around buildings (no clipping).
- 2D admin dashboard, mobile operator app, and 3D tactical view all polling `/api/state`.
- Procedural village generator (`src/video/generate_village.py`) outputs `static/village.ply`.
- 3D view (`/3d`) loads the point-cloud terrain and renders mesh buildings with roofs and labels.

**Still To Do**
- Integrate real PiCrawler robot as Agent 1.
- Record the 3-minute pitch video (OBS or frame capture).
- Final polish: building windows, 3D camera angles, transitions.

### 5.1 Back end

- [x] Create `src/c2/server.py` with Flask.
  - `GET /api/state` — returns simulated mission state.
  - `POST /api/command` — accepts commands, updates simulated state.
  - `GET /video_feed` — MJPEG stream placeholder.
  - `GET /admin` / `/operator` / `/3d` — serve static frontends.
  - `GET /village.ply` — serve procedural village point cloud.
- [x] Simulator inside `server.py`.
  - Procedural village: 10 buildings, roads, drop zone.
  - 5 agents with A*-routed waypoints that avoid buildings.
  - FOV cone geometry and coverage polygon union.
  - Trigger threat at Building 7 and change at Building 3 after set times.
  - Advance state every 200 ms.

### 5.2 Admin dashboard (`src/admin/index.html`)

- [x] Top bar: SCOUT C2 logo, sector, live clock, online status.
- [x] Main tactical map (Canvas):
  - Buildings, roads, grid, green coverage overlay.
  - 5 agent icons with directional arrows and pulsing rings.
  - FOV cones, threat/change markers.
- [x] Right panel:
  - Squad status mini cards.
  - Coverage progress bar.
  - Active alerts list.
  - Command actions: DEPLOY, RECON, RECALL.
- [x] Bottom feeds panel:
  - Live camera feed placeholder, mission log, change log.
- [x] Poll `/api/state` every 500 ms; send commands via `/api/command`.

### 5.2b 3D tactical view (`src/admin/3d.html`)

- [x] Three.js scene with dark tactical background.
- [x] Load `village.ply` point cloud (ground, roads, trees, rocks).
- [x] Render 10 buildings as mesh `BoxGeometry` with roofs and ID labels.
- [x] 5 agent spheres with directional arrows and FOV cones.
- [x] Green coverage circles, threat/change markers.
- [x] Poll `/api/state` every 500 ms.
- [ ] Polish: building windows, cinematic camera angles, atmosphere.

### 5.3 Operator app (`src/operator/index.html`)

- [x] Squad dashboard with minimap, 5 agent cards, coverage bar, quick actions, active alerts.
- [x] Live feed placeholder and command buttons.
- [x] Poll `/api/state` every 500 ms; commands via `/api/command`.
- [ ] Add threat alert modal and change-detection before/after screen (optional).

### 5.4 Shared UI kit

- Inline CSS variables in each HTML file (no build step).
- Colors:
  - BG_PRIMARY `#0A0E1A`, BG_PANEL `#0F1629`, BG_ELEVATED `#141D35`
  - ACCENT_CYAN `#00F0FF`, ACCENT_RED `#FF3366`, ACCENT_YELLOW `#FFCC00`, ACCENT_GREEN `#00FF88`
- Fonts: Inter for body, bold monospace for data.
- Minimum touch target 64 px for operator buttons.

### 5.5 Success Criteria (Met)

- [x] `python src/c2/server.py` starts without errors.
- [x] Admin dashboard shows animated 2D map with 5 moving agents and growing green coverage.
- [x] 3D tactical view loads village and shows mesh buildings + moving agents.
- [x] Operator app shows the squad dashboard and receives state updates.
- [x] Clicking DEPLOY / RECON / RECALL in either UI updates the shared state.
- [x] Threat alert appears automatically at the scripted time.

---

## 6. Next — Video + Polish

**Goal:** Record a cinematic 3-minute pitch video and polish the 3D view.

- [ ] Decide video path:
  - **Option A (fastest):** OBS screen capture of `/3d` + admin overlay in browser.
  - **Option B (automated):** Open3D offscreen render or Three.js frame capture + ffmpeg.
- [ ] Add scene scripting / camera angles to the 3D view or video renderer:
  - Scene 1: Drop (0:00-0:15)
  - Scene 2: Sweep (0:15-0:45)
  - Scene 3: Threat (0:45-1:15)
  - Scene 4: Response / robot deploy (1:15-1:45)
  - Scene 5: Recon / change detection (1:45-2:15)
  - Scene 6: Big picture (2:15-2:45)
  - Scene 7: Close (2:45-3:00)
- [ ] Add admin panel overlay to video frames (HTML overlay or matplotlib composite).
- [ ] Render a 30-second test first, then full 3-minute MP4.
- [ ] Optional: add building windows and atmospheric fog to `/3d`.
- [ ] Run 01-ats evaluator and tune `explorer.py` if score drops.

---

## 7. Robot + Change Detection Integration

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
| UI too complex for 42 h | Operator app is one HTML file; admin uses Canvas; 3D uses Three.js CDN |
| Servo failure | Bring spare servos, calibrate Friday night |

---

## 10. Key Reference Files

- Project context: `edth-munich-2026/CLAUDE.md`
- Pitch script: `edth-munich-2026/docs/PITCH.md`
- Demo flow: `edth-munich-2026/docs/DEMO_SCRIPT.md`
- Hardware checklist: `edth-munich-2026/docs/HARDWARE_CHECKLIST.md`
- 3D research brief: `edth-munich-2026/docs/research/3D_DEMO_RESEARCH_REQUEST.md`

---

*Focus now: record the pitch video and polish the 3D view. Robot integration is next.*
