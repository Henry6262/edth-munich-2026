"""SCOUT C2 — Flask telemetry server + simulator.

Serves:
- /admin          : admin dashboard
- /operator       : field operator mobile app
- /api/state      : mission state JSON
- /api/command    : operator commands
- /video_feed     : MJPEG placeholder stream
"""

from __future__ import annotations

import math
import os
import threading
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional

import cv2
import heapq
import numpy as np
from flask import Flask, Response, jsonify, request, send_from_directory
from shapely.geometry import LineString, Point, Polygon, box
from shapely.ops import unary_union

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIST = os.path.abspath(os.path.join(BASE_DIR, "../../frontend/dist"))
FRONTEND_ASSETS = os.path.join(FRONTEND_DIST, "assets")
app = Flask(__name__, static_folder=None)

MAP_W, MAP_H = 4200, 3200
FOV_R = 170
FOV_DEG = 90
STEP_SIZE = 10.0
EXPLORE_THRESHOLD = 90.0
SURVEIL_THRESHOLD = 90.0

AGENT_COLORS = {
    "A-1": "#00FF88",
    "A-2": "#0088FF",
    "A-3": "#FF8800",
    "A-4": "#FF0088",
    "A-5": "#CCFF00",
}

BUILDINGS = [
    # central village cluster
    {"id": "B1", "x": 1620, "y": 1280, "w": 280, "h": 220},
    {"id": "B2", "x": 2050, "y": 1320, "w": 300, "h": 240},
    {"id": "B3", "x": 1840, "y": 1660, "w": 320, "h": 230},
    {"id": "B4", "x": 1420, "y": 1580, "w": 270, "h": 220},
    # north industrial yard
    {"id": "B5", "x": 1820, "y": 420, "w": 560, "h": 380},
    # east market / checkpoint
    {"id": "B6", "x": 3150, "y": 1260, "w": 430, "h": 320},
    # west church / observation tower
    {"id": "B7", "x": 520, "y": 1260, "w": 320, "h": 340},
    # south logistics outpost
    {"id": "B8", "x": 1950, "y": 2520, "w": 460, "h": 320},
]

ROADS = [
    [(280, 1560), (3920, 1560)],
    [(2100, 260), (2100, 2980)],
    [(620, 2700), (1600, 1940), (2760, 1220), (3650, 900)],
    [(880, 520), (1400, 1240), (1500, 2220)],
]


def _wedge_poly(cx: float, cy: float, angle: float, radius: float, deg: float) -> Polygon:
    pts = [(cx, cy)]
    for a in np.linspace(angle - deg / 2, angle + deg / 2, 25):
        rad = math.radians(a)
        pts.append((cx + radius * math.cos(rad), cy + radius * math.sin(rad)))
    return Polygon(pts)


@dataclass
class Agent:
    id: str
    name: str
    agent_type: str
    color: str
    path: List[tuple]
    idx: int = 0
    x: float = 0.0
    y: float = 0.0
    angle: float = 0.0
    status: str = "PATROLLING"
    battery: int = 78
    signal: int = 92
    detections: int = 0


@dataclass
class SimState:
    agents: List[Agent] = field(default_factory=list)
    coverage: Polygon = field(default_factory=lambda: Polygon())
    coverage_pct: float = 0.0
    alerts: List[dict] = field(default_factory=list)
    mission_log: List[dict] = field(default_factory=list)
    change_log: List[dict] = field(default_factory=list)
    mission_time: float = 0.0
    sector: str = "Sector 7"
    mode: str = "PATROL"
    started_at: float = field(default_factory=time.time)
    threat_triggered: bool = False
    change_triggered: bool = False
    recon_scheduled: bool = False
    recon_started_at: float = 0.0
    recon_finish_at: float = 0.0


class Simulator:
    def __init__(self) -> None:
        self.lock = threading.Lock()
        self.map_bounds = box(0, 0, MAP_W, MAP_H)
        self.state = SimState()
        self._init_agents()
        self._log("MISSION START", "5 agents deployed")
        self.running = True
        self.thread = threading.Thread(target=self._loop, daemon=True)
        self.thread.start()

    def _building_waypoint(self, b: dict, last: tuple) -> tuple:
        """Return a point just outside the building, closest to the previous waypoint."""
        margin = 20.0
        corners = [
            (b["x"] - margin, b["y"] - margin),
            (b["x"] - margin, b["y"] + b["h"] + margin),
            (b["x"] + b["w"] + margin, b["y"] - margin),
            (b["x"] + b["w"] + margin, b["y"] + b["h"] + margin),
        ]
        return min(corners, key=lambda c: math.hypot(c[0] - last[0], c[1] - last[1]))

    def _init_agents(self) -> None:
        names = ["ALPHA", "BRAVO", "CHARLIE", "DELTA", "ECHO"]
        types = ["GROUND", "DRONE", "GROUND", "DRONE", "GROUND"]
        drop = (1200, 100)
        for i, (aid, name, atype) in enumerate(zip(AGENT_COLORS, names, types)):
            # Patrol route: drop -> buildings (outside corners) -> back
            route = [drop]
            for idx in [i, i + 3, i + 6]:
                b = BUILDINGS[idx % len(BUILDINGS)]
                route.append(self._building_waypoint(b, route[-1]))
            route.append(drop)
            path = self._interpolate(route)
            a = Agent(
                id=aid,
                name=name,
                agent_type=atype,
                color=AGENT_COLORS[aid],
                path=path,
                x=drop[0],
                y=drop[1],
                angle=270,
                battery=78 + (i * 3) % 20,
                signal=88 + (i * 2) % 10,
            )
            self.state.agents.append(a)

    def _building_polygons(self, margin: float = 12.0) -> List[Polygon]:
        return [
            box(b["x"] - margin, b["y"] - margin, b["x"] + b["w"] + margin, b["y"] + b["h"] + margin)
            for b in BUILDINGS
        ]

    def _route_segment(self, p1: tuple, p2: tuple) -> List[tuple]:
        """A* route from p1 to p2 avoiding building footprints."""
        # Fast path: no obstacles in the way.
        line = LineString([p1, p2])
        obstacles = getattr(self, "_obstacles", None)
        if obstacles is None:
            obstacles = self._building_polygons(margin=16.0)
            self._obstacles = obstacles
        if not any(line.intersects(o) for o in obstacles):
            return [p1, p2]

        # Grid-based A* with a coarse cell for speed on the bigger map.
        cell = 50.0
        cols, rows = int(math.ceil(MAP_W / cell)), int(math.ceil(MAP_H / cell))
        obstacle_cells = getattr(self, "_obstacle_cells", None)
        if obstacle_cells is None:
            obstacle_cells = set()
            for gx in range(cols):
                for gy in range(rows):
                    cx, cy = gx * cell + cell / 2, gy * cell + cell / 2
                    pt = (cx, cy)
                    if any(o.contains(Point(pt)) for o in obstacles):
                        obstacle_cells.add((gx, gy))
            self._obstacle_cells = obstacle_cells

        def to_grid(p):
            return (int(p[0] // cell), int(p[1] // cell))

        def to_world(g):
            return (g[0] * cell + cell / 2, g[1] * cell + cell / 2)

        start, goal = to_grid(p1), to_grid(p2)
        start = (max(0, min(cols - 1, start[0])), max(0, min(rows - 1, start[1])))
        goal = (max(0, min(cols - 1, goal[0])), max(0, min(rows - 1, goal[1])))
        if start in obstacle_cells:
            obstacle_cells.remove(start)
        if goal in obstacle_cells:
            obstacle_cells.remove(goal)

        # A*.
        open_set = [(0.0, start)]
        came_from = {}
        g_score = {start: 0.0}
        f_score = {start: math.hypot(goal[0] - start[0], goal[1] - start[1])}
        visited = set()
        while open_set:
            _, current = heapq.heappop(open_set)
            if current == goal:
                path = [current]
                while current in came_from:
                    current = came_from[current]
                    path.append(current)
                path.reverse()
                return [p1] + [to_world(g) for g in path[1:]]
            if current in visited:
                continue
            visited.add(current)
            for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1)]:
                nx, ny = current[0] + dx, current[1] + dy
                if nx < 0 or nx >= cols or ny < 0 or ny >= rows:
                    continue
                if (nx, ny) in obstacle_cells:
                    continue
                neighbor = (nx, ny)
                move_cost = math.hypot(dx, dy)
                tentative = g_score[current] + move_cost
                if tentative < g_score.get(neighbor, float("inf")):
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative
                    f_score[neighbor] = tentative + math.hypot(goal[0] - nx, goal[1] - ny)
                    heapq.heappush(open_set, (f_score[neighbor], neighbor))

        # Fallback: straight line if A* fails.
        return [p1, p2]

    def _interpolate(self, waypoints: List[tuple], step: float = STEP_SIZE) -> List[tuple]:
        # Build an obstacle-avoiding polyline through the waypoints.
        routed = [waypoints[0]]
        for (x1, y1), (x2, y2) in zip(waypoints, waypoints[1:]):
            routed.extend(self._route_segment((x1, y1), (x2, y2))[1:])

        # Densify the polyline into small steps.
        pts = [routed[0]]
        for (x1, y1), (x2, y2) in zip(routed, routed[1:]):
            dx, dy = x2 - x1, y2 - y1
            dist = math.hypot(dx, dy)
            if dist == 0:
                continue
            n = max(1, int(dist / step))
            for k in range(1, n + 1):
                t = k / n
                pts.append((x1 + dx * t, y1 + dy * t))
        return pts

    def _log(self, event_type: str, text: str) -> None:
        ts = time.strftime("%H:%M:%S")
        self.state.mission_log.insert(0, {"time": ts, "type": event_type, "text": text})
        self.state.mission_log = self.state.mission_log[:50]

    def _loop(self) -> None:
        while self.running:
            with self.lock:
                self._step()
            time.sleep(0.2)

    def _step(self) -> None:
        self.state.mission_time = time.time() - self.state.started_at
        mt = self.state.mission_time

        # recon scheduler
        if self.state.recon_scheduled and mt > self.state.recon_finish_at:
            self.state.recon_scheduled = False
            self._log("RECON", "Second pass complete")
            if not self.state.change_triggered:
                self.state.change_triggered = True
                self.state.alerts.append(
                    {"type": "CHANGE", "agent": "A-4", "location": "Building 3", "detail": "Door CLOSED → OPEN", "time": time.strftime("%H:%M:%S")}
                )
                self.state.change_log.insert(
                    0, {"time": time.strftime("%H:%M:%S"), "agent": "A-4", "text": "Door OPEN (was CLOSED)"}
                )
                self._log("CHANGE", "A-4 CHANGE — Building 3")

        # scripted threat
        if mt > 45 and not self.state.threat_triggered:
            self.state.threat_triggered = True
            a3 = next(a for a in self.state.agents if a.id == "A-3")
            a3.status = "THREAT"
            a3.angle = 90
            self.state.alerts.append(
                {"type": "THREAT", "agent": "A-3", "location": "Building 7", "confidence": 0.91, "time": time.strftime("%H:%M:%S")}
            )
            self._log("THREAT", "A-3 THREAT — Building 7")

        # move agents
        for a in self.state.agents:
            if a.status in ("HOLD", "THREAT"):
                continue
            if a.idx >= len(a.path) - 1:
                # loop path
                a.idx = 0
            p1 = a.path[a.idx]
            p2 = a.path[a.idx + 1]
            dx, dy = p2[0] - p1[0], p2[1] - p1[1]
            dist = math.hypot(dx, dy)
            if dist > 0:
                a.angle = math.degrees(math.atan2(dy, dx))
            a.x, a.y = p2
            a.idx += 1

            # coverage
            wedge = _wedge_poly(a.x, a.y, a.angle, FOV_R, FOV_DEG)
            try:
                self.state.coverage = unary_union([self.state.coverage, wedge])
            except Exception:
                pass

        # coverage percent
        try:
            covered = self.state.coverage.intersection(self.map_bounds).area
            self.state.coverage_pct = min(100.0, round((covered / self.map_bounds.area) * 100, 1))
        except Exception:
            pass

    def command(self, cmd: str, agent_id: Optional[str] = None) -> None:
        with self.lock:
            cmd = cmd.upper()
            if cmd == "RECALL":
                for a in self.state.agents:
                    a.status = "RECALL"
                    a.path = self._interpolate([(a.x, a.y), (500, 750)])
                    a.idx = 0
                self._log("CMD", "EMERGENCY RECALL all agents")
            elif cmd == "RECON":
                self.state.mode = "RECON"
                self.state.recon_scheduled = True
                self.state.recon_started_at = self.state.mission_time
                self.state.recon_finish_at = self.state.mission_time + 20
                for a in self.state.agents:
                    a.status = "PATROLLING"
                self._log("CMD", "RECON SWEEP ALL ordered")
            elif cmd == "HOLD" and agent_id:
                a = next((x for x in self.state.agents if x.id == agent_id), None)
                if a:
                    a.status = "HOLD"
                    self._log("CMD", f"HOLD ordered for {agent_id}")
            elif cmd == "DEPLOY" and agent_id:
                a = next((x for x in self.state.agents if x.id == agent_id), None)
                if a:
                    a.status = "PATROLLING"
                    # remove threat alert for this agent
                    self.state.alerts = [al for al in self.state.alerts if not (al.get("agent") == agent_id and al["type"] == "THREAT")]
                    self._log("CMD", f"DEPLOY ordered for {agent_id}")
            elif cmd == "MARK":
                self._log("CMD", f"MARK location for {agent_id or 'sector'}")

    def _challenge_goals(self) -> dict:
        recon_window = max(1.0, self.state.recon_finish_at - self.state.recon_started_at)
        if self.state.change_triggered:
            surveil_pct = SURVEIL_THRESHOLD
        elif self.state.recon_scheduled:
            recon_progress = (self.state.mission_time - self.state.recon_started_at) / recon_window
            surveil_pct = min(SURVEIL_THRESHOLD, max(0.0, recon_progress * SURVEIL_THRESHOLD))
        else:
            surveil_pct = 0.0

        ats_phase = "SURVEIL" if self.state.mode == "RECON" or self.state.change_triggered else "EXPLORE"
        if self.state.change_triggered:
            se3_status = "CHANGE DETECTED"
        elif self.state.recon_scheduled:
            se3_status = "SECOND PASS RUNNING"
        else:
            se3_status = "READY FOR SECOND PASS"

        return {
            "ats": {
                "name": "01-ats",
                "title": "3D Graph Exploration & Surveillance",
                "phase": ats_phase,
                "explore_threshold": EXPLORE_THRESHOLD,
                "surveil_threshold": SURVEIL_THRESHOLD,
                "explore_pct": self.state.coverage_pct,
                "surveil_pct": round(surveil_pct, 1),
                "achieved": self.state.coverage_pct >= EXPLORE_THRESHOLD and surveil_pct >= SURVEIL_THRESHOLD,
                "proof": "5 agents observe the unknown zone, then run a second re-observation sweep.",
            },
            "se3": {
                "name": "01-se3",
                "title": "Tactical Intelligence from Live 3D Battlefield Reconstruction",
                "track": "Track 2 change detection + 3D map intelligence layer",
                "status": se3_status,
                "point_cloud": "point_cloud_demo.ply",
                "changes_detected": len(self.state.change_log),
                "achieved": self.state.change_triggered,
                "proof": "The reconstructed battlefield becomes an operator map with threat and change alerts.",
            },
        }

    def get_state(self) -> dict:
        with self.lock:
            return {
                "mission_time": time.strftime("%H:%M:%S", time.gmtime(self.state.mission_time)),
                "elapsed": round(self.state.mission_time, 1),
                "sector": self.state.sector,
                "mode": self.state.mode,
                "coverage_pct": self.state.coverage_pct,
                "agents": [
                    {
                        "id": a.id,
                        "name": a.name,
                        "type": a.agent_type,
                        "color": a.color,
                        "status": a.status,
                        "battery": a.battery,
                        "signal": a.signal,
                        "position": {"x": round(a.x, 1), "y": round(a.y, 1), "angle": round(a.angle, 1)},
                        "fov": {"range": FOV_R, "angle": FOV_DEG},
                    }
                    for a in self.state.agents
                ],
                "buildings": BUILDINGS,
                "roads": ROADS,
                "alerts": list(self.state.alerts),
                "mission_log": list(self.state.mission_log),
                "change_log": list(self.state.change_log),
                "challenge_goals": self._challenge_goals(),
            }


sim = Simulator()


@app.route("/api/state")
def state():
    return jsonify(sim.get_state())


@app.route("/api/command", methods=["POST"])
def command():
    data = request.get_json(force=True, silent=True) or {}
    sim.command(data.get("command", ""), data.get("agent"))
    return jsonify({"ok": True})


@app.route("/video_feed")
def video_feed():
    def generate():
        while True:
            img = np.zeros((480, 640, 3), dtype=np.uint8)
            cv2.putText(img, "SCOUT LIVE FEED", (50, 240), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 255, 0), 2)
            cv2.putText(img, time.strftime("%H:%M:%S"), (50, 280), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 1)
            _, buf = cv2.imencode(".jpg", img)
            yield (b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + buf.tobytes() + b"\r\n")
            time.sleep(0.1)
    return Response(generate(), mimetype="multipart/x-mixed-replace; boundary=frame")


@app.route("/admin")
def admin():
    return send_from_directory(os.path.abspath(os.path.join(BASE_DIR, "../admin")), "index.html")


@app.route("/operator")
def operator():
    return send_from_directory(os.path.abspath(os.path.join(BASE_DIR, "../operator")), "index.html")


@app.route("/3d")
def view_3d():
    return send_from_directory(FRONTEND_DIST, "index.html")


@app.route("/assets/<path:filename>")
def frontend_assets(filename):
    return send_from_directory(FRONTEND_ASSETS, filename)


@app.route("/draco/<path:filename>")
def draco_assets(filename):
    return send_from_directory(os.path.join(FRONTEND_DIST, "draco"), filename)


@app.route("/point_cloud.ply")
def point_cloud():
    return send_from_directory(
        os.path.abspath(os.path.join(BASE_DIR, "../../side-quests/01-se3-change-detection/data")),
        "point_cloud_demo.ply",
    )


@app.route("/village.ply")
def village_ply():
    return send_from_directory(
        os.path.abspath(os.path.join(BASE_DIR, "../../static")),
        "village.ply",
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5050, debug=False, threaded=True)
