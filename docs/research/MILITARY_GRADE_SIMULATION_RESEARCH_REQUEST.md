# Research Request — Military-Grade Tactical Simulation for SCOUT C2

> For: research agent (Claude Opus / Gemini / dedicated research model)
> Context: EDTH Munich 2026 hackathon, SCOUT C2 project
> Deadline: Return an extensive briefing with code, libraries, and an integration plan ASAP.

---

## 1. Current State (Why This Research Is Needed)

We have a working SCOUT C2 prototype:

- **Flask telemetry server** (`src/c2/server.py`) serves live mission state on `http://<ip>:5050/api/state`.
- **2D admin dashboard** (`/admin`) — Canvas map, squad cards, coverage bar, alerts.
- **3D tactical view** (`/3d`) — Three.js buildings, agents, FOV cones.
- **Operator mobile app** (`/operator`) — 2D minimap, agent cards, command buttons.
- **Simulator** (`src/c2/server.py`) moves 5 agents along pre-baked straight-line waypoints.

**The problem:** agents move like robots on rails. They slide in straight lines, ignore building corners, do not pathfind, do not use cover, do not coordinate, and have no tactical awareness. It looks like a basic animation, not a military operation.

**The goal:** upgrade the backend simulator to a **military-grade tactical simulation** where agents move and behave like a real squad:
- Pathfind around buildings using corners and cover.
- Take tactically sound routes (minimize exposure, maximize cover).
- Coordinate as a team (formations, bounding overwatch, sectors of fire).
- React to threats (take cover, suppress, flank, hold, fall back).
- Maintain shared situational awareness (FOV, occlusion, memory, communication).
- Obey high-level commands from the admin/operator UI (DEPLOY, HOLD, RECON, RECALL, MARK).

The frontends stay the same; the **simulator becomes the brain**.

---

## 2. End-State Vision (What We Want to Build)

### 2.1 Movement Layer

Agents move on a **2D tactical plane** (the existing 1000×800 map with building polygons). They must:

- Compute valid paths that avoid building interiors.
- Smoothly navigate around corners and along walls.
- Respect turning radius / acceleration (no instantaneous direction changes).
- Use sidewalks/roads/clearings preferentially.
- Stop at cover positions and peek around corners.

### 2.2 Tactical Behavior Layer

Agents behave like a squad:

- **Formations:** wedge, column, line, diamond based on mission and terrain.
- **Bounding overwatch:** one element moves while others cover.
- **Stacking on corners:** before turning a corner, agents stack and slice the pie.
- **Cover & concealment:** prefer positions behind buildings, walls, vegetation.
- **Threat response:** on contact, agents break contact to nearest cover, return fire, call for support, or assault if ordered.
- **Clearing sectors:** each agent has an assigned sector of fire; FOV cones reflect it.
- **Patrol patterns:** perimeter, linear, zone, figure-eight.

### 2.3 Coordination Layer

- Central commander (the Flask server) assigns goals.
- Agents negotiate who goes where (task allocation / auction / role assignment).
- Shared world model: every agent knows what the team has seen.
- Communication model: line-of-sight radio range, delayed updates if out of contact.

### 2.4 Perception Layer

- **Line-of-sight (LOS):** FOV is blocked by buildings.
- **Occlusion:** agents cannot see through walls.
- **Memory:** areas stay "known" but not currently visible.
- **Threat exposure:** a position is scored by how many enemies can see it.
- **Coverage:** valid coverage is only where at least one agent has current LOS.

### 2.5 Command Layer

High-level commands from UI are translated into tactical plans:

- `DEPLOY A-3` → agent A-3 advances to the threat using cover.
- `HOLD A-3` → A-3 goes to nearest cover and observes.
- `RECON` → squad disperses into a recon formation and sweeps sectors.
- `RECALL` → all agents route back to drop zone using safest paths.
- `MARK` → record a point of interest for strike / investigation.

---

## 3. Research Questions

### 3.1 Pathfinding & Navigation

1. What is the best way to build a **navigation mesh (navmesh)** from 2D building footprints?
   - Triangulation libraries (CDT, poly2tri, shapely + triangle, pymesh, meshpy).
   - Convert shapely polygons to navmesh in Python.
2. Which pathfinding algorithms are best for tactical maps?
   - **A\*** on a grid / visibility graph / navmesh.
   - **Theta\*** / **ANYA** for any-angle pathfinding.
   - **D\* Lite** for dynamic replanning.
   - **RRT\*** for sampling-based pathfinding.
3. How do we add **dynamic obstacles** (other agents, closed doors, new threats)?
4. How do we generate **corner-cutting, smooth paths** rather than jagged grid paths?
5. What Python libraries can do this out-of-the-box?
   - `networkx` + custom visibility graph.
   - `rvo2` (Reciprocal Velocity Obstacles) for collision avoidance.
   - `navmesh` Python package.
   - `pyvisgraph` for visibility graphs.
   - `shapely` + `triangle` for mesh generation.

### 3.2 Tactical Movement & Behavior

1. What are the standard military movement techniques we should implement?
   - Bounding overwatch, traveling overwatch, infiltration, exfiltration.
   - Fire team rushes, peeling, center peel.
2. How do we model **cover and concealment** from a 2D/3D map?
   - Cover map / exposure map.
   - Visibility polygons.
   - Line-of-sight tests (ray casting against building edges).
3. How do agents decide when to move vs. hold vs. engage?
   - Behavior trees vs. finite state machines vs. utility AI.
   - GOAP (Goal-Oriented Action Planning) for high-level planning.
   - HTN (Hierarchical Task Networks) for squad tactics.
4. What are the simplest implementations that still look convincing?
5. Existing code examples:
   - Game AI examples (Unity/Unreal tactical AI).
   - Open-source RTS games (OpenRA, Zero-K, SpringRTS).
   - Military constructive simulations (OneSAF, VBS4 scripting).

### 3.3 Multi-Agent Coordination

1. How do we allocate sectors and waypoints among 5 agents?
   - Market-based task allocation.
   - Voronoi partitioning weighted by risk/cover.
   - Role assignment (point man, cover man, TL, drone operator).
2. How do agents avoid collisions and congestion?
   - ORCA / RVO2.
   - Flow-field pathfinding.
   - Queueing at choke points.
3. How do we model formations?
   - Relative offset positions based on leader and direction.
   - Formation adaptation to terrain width.
4. How do we handle communication loss?
   - Range-limited radio model.
   - Delayed/shared information.

### 3.4 Perception, LOS, and Situational Awareness

1. How to compute **2D visibility polygons** from a point in a polygonal environment?
   - `shapely` ray casting.
   - `pyvisgraph`.
   - `visilibity` C++ library.
2. How to compute **line-of-sight blocked by buildings** efficiently?
3. How to build and update a **coverage map** (grid-based or polygon-based)?
4. How to compute **threat exposure** of a position?
   - Cast rays from threat to position.
   - Compute visible area from threat.
5. How to maintain a **shared tactical picture** across agents?

### 3.5 Integration with Current Stack

1. How should the new simulator replace the current simple one in `src/c2/server.py`?
2. What data structures should be added to `/api/state`?
   - Navmesh polygons.
   - Agent paths (list of waypoints for UI rendering).
   - Cover positions.
   - Threat exposure scores.
   - Formation state.
3. How do we keep the simulation fast enough to run at 5–10 Hz?
4. How do we render the new agent paths in:
   - 2D Canvas admin (`/admin`).
   - Three.js 3D view (`/3d`).
   - Mobile operator minimap (`/operator`).

### 3.6 Evaluation

1. What metrics define "military-grade" movement?
   - Path length vs. exposure.
   - Time to cover.
   - Collisions with walls/agents.
   - Time agents spend in cover.
2. How do we visually/quantitatively test realism?
3. Are there benchmark maps or scenarios we can use?

---

## 4. Deliverables

Please produce a comprehensive research brief saved to:

```
edth-munich-2026/docs/research/MILITARY_GRADE_SIMULATION_BRIEF.md
```

The brief must include:

1. **Recommended architecture** for the simulator (data flow from map → navmesh → planner → behavior → state API).
2. **Recommended Python libraries** with install commands and why they were chosen.
3. **Code snippets** for:
   - Generating a navmesh from shapely building polygons.
   - A* / Theta* pathfinding on that navmesh.
   - Visibility polygon / LOS check.
   - ORCA / RVO2 collision avoidance.
   - Formation controller.
   - Behavior tree / FSM for an agent.
4. **Step-by-step migration plan** from the current simple simulator to the new one.
5. **File layout** showing where each new module goes in `edth-munich-2026/src/c2/`.
6. **List of open-source projects** we can borrow from, with links and notes on what to extract.
7. **Papers / articles** to read for deeper understanding.
8. **Fallback plan** if full tactical AI is too complex for the remaining hours.

---

## 5. Resources to Find

Search for and include direct links to:

### 5.1 Python libraries
- `rvo2` (ORCA implementation) — GitHub / PyPI.
- `pyvisgraph` — visibility graph.
- `navmesh` / `pynavmesh`.
- `triangle` / `meshpy` / `cdt` for constrained Delaunay triangulation.
- `shapely` advanced operations (visibility, buffer, skeleton).

### 5.2 Algorithms & tutorials
- A* on navmesh tutorial.
- Theta* / ANYA pathfinding.
- Visibility polygon algorithms (Bentley-Ottmann, ray sweep).
- Reciprocal Velocity Obstacles (RVO) explained.
- Behavior trees in Python (`py_trees`, `behavior3py`).
- GOAP / HTN Python implementations.

### 5.3 Open-source games / sims
- OpenRA AI.
- Zero-K / SpringRTS pathfinding and unit AI.
- WarMUX / Hedgewars.
- Arma 3 AI modding wiki.
- VBS4 scripting manual (if publicly available).
- OneSAF / JCATS overview (conceptual).
- ROS2 Nav2 behavior trees / planner server.

### 5.4 Academic references
- "A*, Theta*: Any-Angle Path Planning on Grids" Nash et al.
- "Reciprocal Velocity Obstacles for Real-Time Multi-Agent Navigation" van den Berg et al.
- "Optimal Reciprocal Collision Avoidance (ORCA)" van den Berg et al.
- "An Overview of Real-Time Strategy Game AI" Robertson & Watson.
- Military doctrine references for small-unit tactics (FM 3-21.8, ATP 3-21.8).

### 5.5 Existing map / scenario data
- Urban tactical maps (SVG, GeoJSON, shapefiles).
- Procedural city generators that output polygons.

---

## 6. Constraints

- Must integrate with existing Flask state API.
- Must run offline on a laptop.
- Must be fast enough for real-time demo (5–10 Hz updates).
- Must not require Unity/Unreal/Godot for the core simulator (browser 3D is separate).
- Prefer Python + stdlib + existing libraries; avoid heavy ML training.
- We have limited hours — prioritize the biggest visual and tactical wins first.

---

## 7. Current Project Files

- `edth-munich-2026/src/c2/server.py` — current simulator + Flask server.
- `edth-munich-2026/src/admin/index.html` — 2D dashboard.
- `edth-munich-2026/src/admin/3d.html` — 3D view.
- `edth-munich-2026/src/operator/index.html` — mobile app.
- `edth-munich-2026/docs/IMPLEMENTATION_PLAN.md` — current build plan.
- `edth-munich-2026/docs/research/3D_DEMO_RESEARCH_REQUEST.md` — 3D research request.

---

*Goal: turn the current slide-show animation into a believable tactical simulation that wins the demo.*
