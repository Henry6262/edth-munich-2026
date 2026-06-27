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
import numpy as np
from flask import Flask, Response, jsonify, request, send_from_directory
from shapely.geometry import Polygon, box
from shapely.ops import unary_union

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app = Flask(__name__, static_folder=None)

MAP_W, MAP_H = 1000, 800
FOV_R = 90
FOV_DEG = 90
STEP_SIZE = 5.0

AGENT_COLORS = {
    "A-1": "#00FF88",
    "A-2": "#0088FF",
    "A-3": "#FF8800",
    "A-4": "#FF0088",
    "A-5": "#CCFF00",
}

BUILDINGS = [
    {"id": "B1", "x": 80, "y": 80, "w": 90, "h": 70},
    {"id": "B2", "x": 280, "y": 120, "w": 110, "h": 80},
    {"id": "B3", "x": 480, "y": 70, "w": 100, "h": 90},
    {"id": "B4", "x": 180, "y": 320, "w": 130, "h": 100},
    {"id": "B5", "x": 440, "y": 280, "w": 90, "h": 110},
    {"id": "B6", "x": 680, "y": 180, "w": 120, "h": 90},
    {"id": "B7", "x": 130, "y": 520, "w": 110, "h": 80},
    {"id": "B8", "x": 390, "y": 470, "w": 140, "h": 100},
    {"id": "B9", "x": 640, "y": 440, "w": 100, "h": 120},
    {"id": "B10", "x": 790, "y": 590, "w": 110, "h": 90},
]

ROADS = [
    [(50, 400), (950, 400)],
    [(500, 50), (500, 750)],
    [(150, 200), (850, 600)],
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

    def _init_agents(self) -> None:
        centers = [(b["x"] + b["w"] / 2, b["y"] + b["h"] / 2) for b in BUILDINGS]
        names = ["ALPHA", "BRAVO", "CHARLIE", "DELTA", "ECHO"]
        types = ["GROUND", "DRONE", "GROUND", "DRONE", "GROUND"]
        drop = (500, 750)
        for i, (aid, name, atype) in enumerate(zip(AGENT_COLORS, names, types)):
            # simple route: drop -> a few buildings -> back
            route = [drop, centers[i % len(centers)], centers[(i + 3) % len(centers)], centers[(i + 6) % len(centers)], drop]
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

    def _interpolate(self, waypoints: List[tuple], step: float = STEP_SIZE) -> List[tuple]:
        pts = [waypoints[0]]
        for (x1, y1), (x2, y2) in zip(waypoints, waypoints[1:]):
            dx, dy = x2 - x1, y2 - y1
            dist = math.hypot(dx, dy)
            if dist == 0:
                continue
            n = max(1, int(dist / step))
            for k in range(1, n + 1):
                t = k / n
                pts.append((x1 + dx * t, y2 - (y2 - y1) * (1 - t)))
            pts.append((x2, y2))
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
    return send_from_directory(os.path.abspath(os.path.join(BASE_DIR, "../admin")), "3d.html")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5050, debug=False, threaded=True)
