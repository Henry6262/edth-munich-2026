# SCOUT — 3-Minute Demo Script

## Setup

- Large table
- Tape path on table (colored electrical tape)
- 3 cardboard boxes as "sectors"
- Black cardboard drone cutout on a stick
- PiCrawler robot at start of tape path
- Laptop showing Streamlit dashboard
- All cameras connected and powered

## Demo Flow

### Phase 1: PATROL / EXPLORE (0:40–1:10)

1. Say: "SCOUT begins autonomous exploration of the perimeter."
2. Start robot walking the tape path.
3. Dashboard shows: "PATROL — Sector 1... Sector 2... Sector 3..."
4. Camera feed switches between overwatch and AI targeting views.

### Phase 2: DETECT & TRACK (1:10–1:50)

1. Hold drone cutout in front of the AI camera.
2. Robot STOPS and turns toward the drone.
3. Dashboard flashes: "🚨 UAV DETECTED — Type: Quadcopter, Confidence: 94%, Tracking..."
4. Move drone slowly left/right.
5. Robot turns to keep drone centered in frame.
6. Say: "SCOUT maintains visual lock. This is Positive Identification before engagement."

### Phase 3: REPORT & SCALE (1:50–2:40)

1. Dashboard shows threat log: timestamp, sector, UAV type, confidence.
2. Say: "SCOUT reports the threat to command. No cloud, no latency, no data leak."
3. Say: "Current counter-UAS: $500K radar, one per base, doesn't work indoors or against fiber-optic drones. SCOUT: €200, deploy 100 per base."
4. Remove drone cutout.
5. Robot returns to patrol or holds position.

### Phase 4: CLOSE (2:40–3:00)

1. Say: "Built in 42 hours at EDTH Munich. Challenge 01-ats: 3D graph exploration and surveillance, demonstrated on a walking quadruped."
2. Final dashboard screen: mission complete, sectors clear.

## Contingencies

- **Robot falls off table:** Use large table, add edge boxes, practice beforehand.
- **Camera doesn't detect drone:** Use high-contrast black cardboard, ensure good lighting.
- **WiFi fails:** Run dashboard on localhost via Ethernet or direct connection.
- **Robot servo fails:** Bring spare servos.
- **Demo freezes:** Have a video backup of the robot working.

## Backup Plan

If robot hardware fails entirely:
1. Show recorded video of robot walking and detecting.
2. Run challenge evaluation live: `uv run run_eval.py --submission src/algorithm/explorer.py --graphs graphs/train/basic.json --viz`
3. Show the 3D Rerun visualization of the algorithm.
