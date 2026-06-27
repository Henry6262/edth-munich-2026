# SCOUT — 3-Minute Demo Script

## Setup

- Large table
- Tape path on table (colored electrical tape)
- 3 cardboard boxes as "sectors"
- Black cardboard drone cutout on a stick
- PiCrawler robot at start of tape path
- Laptop showing SCOUT C2 dashboard (open `/admin` and `/3d` in two browser tabs)
- Phone showing operator app at `/operator`
- All cameras connected and powered
- Pre-recorded 3D pitch video loaded as backup

## Demo Flow

### Phase 1: PATROL / EXPLORE (0:40–1:10)

1. Say: "SCOUT begins autonomous exploration of the perimeter."
2. Start robot walking the tape path.
3. Admin dashboard shows: "PATROL — Sector 1... Sector 2... Sector 3..." with agents moving and green coverage growing.
4. Switch to the 3D view tab: show five agents sweeping the procedural village, FOV cones painting coverage.
5. Camera feed switches between overwatch and AI targeting views.

### Phase 2: DETECT & TRACK (1:10–1:50)

1. Hold drone cutout / red card in front of the AI camera.
2. Robot STOPS and turns toward the drone.
3. Admin dashboard flashes: "🚨 UAV DETECTED — Type: Quadcopter, Confidence: 94%, Tracking..."
4. Move drone slowly left/right.
5. Robot turns to keep drone centered in frame.
6. Say: "SCOUT maintains visual lock. This is Positive Identification before engagement."

### Phase 3: RECON / CHANGE DETECTION (1:50–2:20)

1. Say: "Two hours later, SCOUT runs a second recon pass."
2. Show the 3D view again: agents resweep the village.
3. Switch to admin dashboard: yellow alert "CHANGE — Building 3, door CLOSED → OPEN."
4. Show before/after images from `change_detector.py` if available.
5. Say: "SCOUT spots what changed, not just what moves."

### Phase 4: REPORT & SCALE (2:20–2:50)

1. Dashboard shows threat log: timestamp, sector, UAV type, confidence.
2. Say: "SCOUT reports the threat to command. No cloud, no latency, no data leak."
3. Say: "Current counter-UAS: $500K radar, one per base, doesn't work indoors or against fiber-optic drones. SCOUT: €200, deploy 100 per base."
4. Remove drone cutout.
5. Robot returns to patrol or holds position.

### Phase 5: CLOSE (2:50–3:00)

1. Say: "Built in 42 hours at EDTH Munich. Challenge 01-ats: 3D graph exploration and surveillance. SE3 Labs Track 2: tactical change detection. Demonstrated on a walking quadruped and a live C2 dashboard."
2. Final dashboard screen: mission complete, sectors clear.

## Contingencies

- **Robot falls off table:** Use large table, add edge boxes, practice beforehand.
- **Camera doesn't detect drone/card:** Use high-contrast colors, ensure good lighting.
- **WiFi fails:** Run dashboard on localhost via Ethernet or direct connection.
- **Robot servo fails:** Bring spare servos.
- **Demo freezes:** Have the pre-recorded 3D pitch video ready to play.
- **3D view lags:** Switch to the 2D admin dashboard; it shows the same data.

## Backup Plan

If robot hardware fails entirely:
1. Play the pre-recorded 3D pitch video (`/3d` screen capture).
2. Show the live admin dashboard and operator app running in simulation.
3. Run challenge evaluation live: `uv run run_eval.py --submission src/algorithm/explorer.py --graphs graphs/train/basic.json --viz`
4. Run change detection live: `python side-quests/01-se3-change-detection/change_detector.py before.jpg after.jpg output.jpg`
