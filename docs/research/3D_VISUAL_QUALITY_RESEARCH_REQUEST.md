# Research Request: SCOUT C2 3D Tactical View — Visual Quality & Readability

## Project Context

SCOUT C2 is a hackathon demo for EDTH Munich 2026. It consists of:
- A Flask backend (`src/c2/server.py`) simulating 5 agents patrolling a 1000×800 procedural village.
- A 2D admin dashboard (`/admin`) showing the tactical map.
- A 3D tactical view (`/3d`) built with Three.js r128, loading a procedural PLY point cloud and rendering buildings, agents, FOV cones, coverage trails, and alerts.
- A mobile operator app (`/operator`).

The goal of the 3D view is to look like a **Rainbow Six Siege-style "god camera"** — readable, cinematic, and game-like — for a pitch video and live demo.

## What We Have Built So Far

### Procedural village generator (`src/video/generate_village.py`)
- Outputs `static/village.ply` (~90K points).
- Contains ground, roads, trees, rocks.
- Buildings are intentionally excluded from the point cloud and rendered as separate mesh geometry.

### 3D view (`src/admin/3d.html`)
- Loads PLY via `THREE.PLYLoader`.
- Creates 10 mesh buildings (`BoxGeometry`) with transparent volumes, wireframe edges, roofs, window planes, and ID labels.
- Creates 5 agent groups made of simple BoxGeometry/SphereGeometry humanoids (torso, head, visor, weapon, arms, legs).
- Adds a glowing ring, point light, and vertical beacon pillar above each agent.
- Renders flat vision wedges + center laser lines for FOV.
- Adds trailing path lines (glow + core) behind agents.
- Adds green coverage circles on the ground.
- Adds road meshes with dashed center lines.
- Adds a Canvas2D tactical minimap.
- Implements client-side interpolation for smooth agent movement between 500ms state polls.
- Adds walking animation (leg swing + body bob).

### Reference demo
Another agent produced a standalone indoor tactical map demo at:
`/Users/henry/Downloads/opearator-packs/tactical_map_demo.html`

That demo uses:
- Colored point cloud by height (floor/blue, walls/green, ceiling/orange).
- Transparent room boxes with wireframe edges.
- Glowing robot icon with pulse ring.
- Room state UI panel.
- 3-point lighting + fog.

It looks more readable than our current 3D village, but it is designed for indoor rooms, not an outdoor village.

## What We Are Struggling With

### 1. Agent readability
Despite scaling agents 2.5x, adding emissive materials, point lights, and beacon pillars, the humanoid agents are still hard to see against the terrain. They tend to look like tiny dark specks or disappear entirely depending on camera angle and lighting.

**Questions:**
- What is the correct visual hierarchy for a tactical god-camera view? Should agents be icons, silhouettes, or full models?
- How do successful games (R6 Siege drone cam, Door Kickers, Zero Hour, XCOM) represent operators on a 3D map?
- Should we use billboard sprites, glowing chevrons, or simplified "miniature" models?
- What color/brightness/contrast values ensure agents pop against dark terrain?

### 2. Point cloud quality
The PLY point cloud looks like sparse dots rather than a dense, readable terrain. It does not classify points into semantic layers (floor, wall, vegetation) because it is an outdoor village.

**Questions:**
- For an outdoor tactical map, should the ground be a textured mesh instead of a point cloud?
- How do we make the point cloud look like a LiDAR scan rather than scattered noise?
- What point size, opacity, color grading, and density work best for readability?
- Should we abandon the PLY point cloud entirely for the demo and use a hand-authored mesh/terrain?

### 3. Environment visual appeal
The village currently looks like gray blocks on a blue grid. Buildings lack detail, roads are simple planes, and there is no atmosphere.

**Questions:**
- What is the fastest way to make 10 procedurally placed buildings look like a real village? (windows, doors, roofs, damage, props)
- How do we add atmosphere without killing performance? (fog, particles, light shafts, color grading)
- What low-poly environment props add the most realism per effort? (fences, walls, barrels, vehicles, vegetation)
- Should we use a satellite-style ground texture under a sparse point cloud?

### 4. Camera and cinematic feel
The default orbit camera is static and does not emphasize the action.

**Questions:**
- What camera modes do tactical games use for spectator/god views?
- How do we implement smooth follow-cam, action snaps, and cinematic orbit?
- What post-processing is essential for a "game-like" look? (bloom, SSAO, color grading)
- Can we achieve a compelling look without WebGL post-processing (for performance)?

### 5. Tactical movement and behavior
Agents currently walk directly between waypoints with basic interpolation. They do not look like a coordinated squad.

**Questions:**
- What simple behaviors make AI agents look tactical? (cover, stacking, bounding, speed variation, stances)
- How do we animate simple BoxGeometry humanoids to look like they are walking/crouching/sprinting without external animation assets?
- What visual cues communicate intent? (planned path lines, stance icons, hand signals)

## What We Need

1. **Concrete examples**: Links to Three.js examples, game screenshots, or codepens that achieve a readable tactical 3D view.
2. **Best practices**: Specific values for lighting, fog, colors, point sizes, and camera settings for a dark tactical theme.
3. **Asset-light techniques**: Procedural or code-generated ways to add detail without needing Blender/GLB assets.
4. **Alternative approaches**: If our current point-cloud + BoxGeometry approach is fundamentally wrong, tell us what to pivot to.
5. **Priority ranking**: Which 2-3 changes will give the biggest visual upgrade for the least effort?

## Constraints

- Must run in a browser with Three.js (no build step preferred).
- Must run at 60 FPS on a MacBook Pro with ~90K point cloud + 10 buildings + 5 agents.
- No external 3D artists or long asset pipelines available.
- Demo is in ~24-48 hours.

## Deliverables

- Written assessment of what is wrong with the current approach.
- Shortlist of 3-5 recommended changes with estimated effort.
- Code snippets or pseudocode for the top 2 recommendations.
- Reference images / links.
