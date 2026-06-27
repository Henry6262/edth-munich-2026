# Research Request — SCOUT C2 3D Demo Upgrade

> For: research agent (Claude / Gemini / dedicated research model)  
> Context: EDTH Munich 2026 hackathon, SCOUT C2 project  
> Deadline: Return a concise recommendation + integration plan ASAP (we have limited hours before demo).

---

## 1. Current State (What Already Works)

We have a **working 2D tactical command system** running locally:

- **Flask telemetry server**: `edth-munich-2026/src/c2/server.py`
  - `GET /api/state` returns live mission state: 5 agents, positions, status, battery, FOV, coverage %, alerts, mission log.
  - `POST /api/command` accepts DEPLOY / HOLD / RECON / RECALL / MARK.
  - `GET /video_feed` serves an MJPEG placeholder stream.
  - Runs on `http://<laptop-ip>:5050`.
- **Admin dashboard**: `edth-munich-2026/src/admin/index.html` — 2D Canvas map + squad panel.
- **Operator mobile app**: `edth-munich-2026/src/operator/index.html` — mobile web UI.
- **Simulator**: Python backend drives 5 agents on a 2D village with buildings, roads, FOV cones, green coverage, scripted threat/change alerts.
- **01-ats algorithm**: `src/algorithm/explorer.py` — 3D graph exploration policy (produces waypoints).
- **01-se3 change detection**: `side-quests/01-se3-change-detection/change_detector.py` — OpenCV change detector.

The **research agent conversation package** is at:
- `/Users/henry/Downloads/Kimi_Agent_机器人防御挑战 (1)/`
- Especially relevant: `SE3_REAL_DATA_GUIDE.md`, `THE_PLAN.md`, `C2_TACTICAL_COMMAND_SYSTEM.md`, `DESIGN_SYSTEM_AND_SCREENS.md`.

---

## 2. The Problem

The demo currently shows a **2D tactical map**. For EDTH Munich, the SE3 Labs challenge is explicitly about **3D battlefield reconstruction**. A 3D demo is significantly more impressive and directly validates SE3's technology.

**We need to upgrade the demo to 3D** while preserving the working admin/operator apps and Flask state API.

---

## 3. Research Questions

Please answer the following with concrete recommendations, trade-offs, and code/file paths where possible.

### 3.1 3D Map Data

- What is the fastest way to get or generate a **3D village scene** for the demo?
  - Option A: Use SE3 Labs data at the event (`.ply` point clouds, `.glb` meshes, camera poses). How do we obtain it? Who is the contact (Alexander Hobmeier)? What format exactly?
  - Option B: Generate a procedural 3D village with Open3D (code in `SE3_REAL_DATA_GUIDE.md`). How many points/buildings can we render smoothly in a browser?
  - Option C: Use DUSt3R / MASt3R on a small set of drone/tabletop photos to reconstruct a real scene. Is this feasible in a few hours?
- **Option D — Drone video → 3D reconstruction**:
  - Find a suitable royalty-free / Creative Commons drone video flying over a village, base, or compound.
  - Run it through **DUSt3R** or **MASt3R** to produce a `.ply` point cloud / mesh.
  - What are the exact commands / Colab notebooks / GitHub repos to do this in under an hour?
  - What video length/quality is needed? How many frames should be sampled?
  - Where can we find a good video? (YouTube, Pexels, Pixabay, Wikimedia, etc.)
  - What are the licensing constraints for hackathon demo use?
- Which format should we target for the renderer: `.ply`, `.glb`/`.gltf`, or convert to a custom Three.js scene?

### 3.2 3D Rendering Stack

- **Browser-based 3D (admin + operator)**:
  - Three.js vs. Rerun web viewer vs. Open3D web visualizer vs. Babylon.js?
  - Which is fastest to integrate with our Flask state API (polling `/api/state` and updating agent positions)?
  - Which works on a phone browser (operator app) without heavy GPU requirements?
  - How do we render a point cloud efficiently in Three.js (e.g., `THREE.Points`, decimation, level-of-detail)?
- **Offline 3D video rendering**:
  - Best path to generate a **3-minute cinematic MP4** from a 3D scene:
    - Open3D off-screen rendering + ffmpeg?
    - Rerun recording + export?
    - Blender Python scripting?
    - OBS screen capture of a running Open3D/Rerun window?
  - How do we add an admin overlay (text, coverage %, agent statuses) onto the rendered frames?
  - How do we synchronize the 3D animation timing with the demo script (drop, sweep, threat, response, recon, big picture, close)?

### 3.3 Agent Representation in 3D

- How do we represent the 5 agents on the 3D terrain?
  - Simple colored spheres? Quadruped/robot model for Agent 1? Drone model for Agents 2/4?
  - Where to get lightweight 3D models (glTF) that load fast in a browser?
  - How do we orient agents to face their movement direction on 3D terrain?
- How do we render **FOV cones** in 3D and accumulate **coverage zones** on the ground?
  - Should coverage be a projected circle on the terrain, a translucent cone, or a decal?
  - How do we compute coverage percentage in 3D?

### 3.4 Threat / Change Markers in 3D

- How do we place red/yellow alert markers on 3D buildings?
  - Billboard sprites, 3D icons, or HTML overlays?
  - How do we map "Building 7" from our 2D building list to a 3D structure?
- For change detection: how do we show a before/after comparison when the scene is 3D?
  - Show two camera views side-by-side?
  - Highlight changed regions in the 3D point cloud?

### 3.5 Integration with Existing System

- How should the 3D frontend receive state updates from Flask?
  - Keep polling `/api/state` every 500 ms and update Three.js object transforms?
  - Or switch to Server-Sent Events / WebSocket for smoother animation?
- Should the 3D renderer live in the existing `src/admin/index.html` and `src/operator/index.html`, or in a separate `/3d` route?
- How do we fall back to 2D if 3D fails on a device or at the venue?

### 3.6 Performance & Phone Constraints

- What is the maximum point cloud size (points) we can render at 30 FPS on:
  - A laptop browser (admin)?
  - A modern phone browser (operator)?
- What decimation/simplification techniques should we use?
- Should the operator 3D view be a simplified version (low-res point cloud, fewer effects) compared to the admin view?

---

## 4. Resources to Find

Please search for and include direct links to:

### 4.1 Drone footage for 3D reconstruction
- Free / CC0 / CC-BY drone videos of villages, compounds, military bases, or urban areas.
- Good sources: Pexels, Pixabay, Coverr, Mixkit, Wikimedia Commons, YouTube Creative Commons.
- Preferred: slow, stable flight with good overlap; 30–60 seconds; daytime; no motion blur.
- Include search queries used and the exact license of each candidate video.

### 4.2 3D reconstruction tools
- **DUSt3R** GitHub repo and quick-start: `https://github.com/naver/dust3r`
- **MASt3R** GitHub repo: `https://github.com/naver/mast3r`
- Colab notebooks that run DUSt3R / MASt3R on a video.
- Tutorials for converting video frames → `.ply` point cloud.
- Alternatives: `meshroom`, `colmap`, `nerfstudio`, `gaussian-splatting`.

### 4.3 Browser 3D rendering
- Three.js point-cloud examples and loaders (`PLYLoader`, `GLTFLoader`).
- Rerun SDK web viewer and recording API.
- Open3D web visualizer (if any).
- Babylon.js point cloud examples.

### 4.4 Offline 3D video rendering
- Open3D off-screen rendering / headless camera capture.
- Rerun recording and video export.
- Blender Python scripting for camera animation + rendering.
- FFmpeg composition of frames + overlay.

### 4.5 Lightweight 3D assets
- Free glTF models for quadruped robot, drone, human figure, buildings.
- Sources: Sketchfab (CC), Poly Pizza, Kenney assets, Three.js examples.

---

## 6. Deliverables

Please produce a concise research brief (1–3 pages) with:

1. **Recommended 3D stack** for our scenario (browser + offline video), with justification.
2. **Step-by-step integration plan** into `edth-munich-2026/src/c2/server.py`, `src/admin/index.html`, and `src/operator/index.html`.
3. **Code snippets** for:
   - Loading a `.ply` point cloud in the browser.
   - Updating agent positions from `/api/state`.
   - Rendering FOV cones / coverage zones.
   - Exporting a 3-minute video from the chosen renderer.
4. **Fallback strategy** if 3D is too slow or SE3 data is unavailable.
5. **List of dependencies** to install and estimated setup time.
6. **Specific file paths** in the project where each piece should go.

---

## 7. Constraints

- Must work **offline** at the venue — no cloud rendering services.
- Must run on **local Wi-Fi/hotspot**.
- Operator app must work on a **phone browser**.
- We cannot spend more than a few hours on 3D integration — prefer the simplest path that looks impressive.
- The 01-ats `Explorer` class produces **3D graph waypoints** (x, y, z) — we should use them if possible.
- Keep the existing Flask state API contract; only extend it if necessary.

---

## 8. Output Location

Write the research brief to:

```
edth-munich-2026/docs/research/3D_DEMO_RESEARCH_BRIEF.md
```

And update `edth-munich-2026/docs/IMPLEMENTATION_PLAN.md` if the 3D plan replaces or extends tonight's focus.
