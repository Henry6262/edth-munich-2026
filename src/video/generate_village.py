"""Generate a procedural village point cloud for the SCOUT C2 3D view.

Output: static/village.ply
Coordinates match the simulator map (1000 x 800 ground plane).
PLY uses Y-up: x = simulator x, y = height, z = simulator y.
"""

from __future__ import annotations

import os
import random
from typing import List, Tuple

import numpy as np

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(BASE_DIR, "../.."))
OUT_PATH = os.path.join(ROOT, "static", "village.ply")

MAP_W, MAP_H = 1000.0, 800.0

# Same buildings as the simulator so agents and alerts line up.
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

# Palette (RGB 0-255)
COLORS = {
    "ground": np.array([45, 50, 40]),
    "ground_dark": np.array([38, 43, 34]),
    "road": np.array([75, 72, 66]),
    "road_light": np.array([90, 87, 80]),
    "building": np.array([95, 100, 110]),
    "building_dark": np.array([75, 80, 90]),
    "roof": np.array([110, 70, 60]),
    "tree": np.array([45, 110, 55]),
    "tree_dark": np.array([35, 90, 45]),
    "trunk": np.array([80, 60, 45]),
    "rock": np.array([80, 78, 72]),
}


def jitter(color: np.ndarray, amount: float = 12.0) -> np.ndarray:
    """Add small per-point color variation."""
    c = color.astype(np.float32) + np.random.normal(0, amount, 3)
    return np.clip(c, 0, 255).astype(np.uint8)


def add_points(points: List[Tuple[float, float, float, int, int, int]], xs, ys, zs, color) -> None:
    """Append a batch of points with shared base color."""
    n = len(xs)
    cols = np.tile(color.astype(np.uint8), (n, 1))
    cols = np.clip(cols.astype(np.int16) + np.random.randint(-10, 11, size=(n, 3)), 0, 255).astype(np.uint8)
    for x, y, z, r, g, b in zip(xs, ys, zs, cols[:, 0], cols[:, 1], cols[:, 2]):
        points.append((float(x), float(y), float(z), int(r), int(g), int(b)))


def generate_ground(points: List[Tuple[float, float, float, int, int, int]], target: int = 12000) -> None:
    """Uneven dirt ground plane."""
    xs = np.random.uniform(0, MAP_W, target)
    zs = np.random.uniform(0, MAP_H, target)
    # gentle rolling height
    ys = (
        0.8 * np.sin(xs / 180.0) * np.cos(zs / 140.0)
        + 0.4 * np.sin(xs / 60.0 + zs / 80.0)
        + np.random.normal(0, 0.15, target)
    )
    base_keys = np.random.choice(["ground", "ground_dark"], size=target)
    base = np.array([COLORS[k] for k in base_keys])
    cols = np.clip(base.astype(np.int16) + np.random.randint(-8, 9, size=(target, 3)), 0, 255).astype(np.uint8)
    for x, y, z, c in zip(xs, ys, zs, cols):
        points.append((float(x), float(y), float(z), int(c[0]), int(c[1]), int(c[2])))


def generate_roads(points: List[Tuple[float, float, float, int, int, int]], samples_per_unit: float = 0.8) -> None:
    """Dirt roads with tyre-track scarring."""
    for road in ROADS:
        (x1, y1), (x2, y2) = road
        length = np.hypot(x2 - x1, y2 - y1)
        n = max(20, int(length * samples_per_unit))
        t = np.linspace(0, 1, n)
        cx = x1 + (x2 - x1) * t
        cz = y1 + (y2 - y1) * t
        # road width ~14 units
        width = 14.0
        perp_x = -(y2 - y1) / length if length > 0 else 0
        perp_y = (x2 - x1) / length if length > 0 else 0
        offsets = np.random.uniform(-width / 2, width / 2, n)
        px = cx + perp_x * offsets
        pz = cz + perp_y * offsets
        py = 0.05 + np.random.normal(0, 0.08, n)
        base_keys = np.random.choice(["road", "road_light"], size=n)
        base = np.array([COLORS[k] for k in base_keys])
        cols = np.clip(base.astype(np.int16) + np.random.randint(-6, 7, size=(n, 3)), 0, 255).astype(np.uint8)
        for x, y, z, c in zip(px, py, pz, cols):
            points.append((float(x), float(y), float(z), int(c[0]), int(c[1]), int(c[2])))


def generate_buildings(points: List[Tuple[float, float, float, int, int, int]]) -> None:
    """Simple box buildings with flat roofs."""
    for b in BUILDINGS:
        x0, y0, w, h = b["x"], b["y"], b["w"], b["h"]
        height = random.uniform(22.0, 50.0)
        # wall points
        n_wall = 1200
        side = random.choice(["x", "z"])
        xs = np.random.uniform(x0, x0 + w, n_wall)
        zs = np.random.uniform(y0, y0 + h, n_wall)
        # keep only perimeter
        mask = (xs < x0 + 1.5) | (xs > x0 + w - 1.5) | (zs < y0 + 1.5) | (zs > y0 + h - 1.5)
        xs = xs[mask]
        zs = zs[mask]
        ys = np.random.uniform(0, height, len(xs))
        base_keys = np.random.choice(["building", "building_dark"], size=len(xs))
        base = np.array([COLORS[k] for k in base_keys])
        cols = np.clip(base.astype(np.int16) + np.random.randint(-8, 9, size=(len(xs), 3)), 0, 255).astype(np.uint8)
        for x, y, z, c in zip(xs, ys, zs, cols):
            points.append((float(x), float(y), float(z), int(c[0]), int(c[1]), int(c[2])))

        # roof
        n_roof = 400
        xs = np.random.uniform(x0 + 1, x0 + w - 1, n_roof)
        zs = np.random.uniform(y0 + 1, y0 + h - 1, n_roof)
        ys = np.full(n_roof, height) + np.random.normal(0, 0.2, n_roof)
        cols = np.tile(COLORS["roof"], (n_roof, 1))
        cols = np.clip(cols.astype(np.int16) + np.random.randint(-10, 11, size=(n_roof, 3)), 0, 255).astype(np.uint8)
        for x, y, z, c in zip(xs, ys, zs, cols):
            points.append((float(x), float(y), float(z), int(c[0]), int(c[1]), int(c[2])))


def generate_trees(points: List[Tuple[float, float, float, int, int, int]], n_trees: int = 60) -> None:
    """Scattered tree clusters avoiding buildings."""
    building_boxes = [(b["x"] - 8, b["y"] - 8, b["x"] + b["w"] + 8, b["y"] + b["h"] + 8) for b in BUILDINGS]

    def inside_building(x: float, z: float) -> bool:
        return any(x0 <= x <= x1 and y0 <= z <= y1 for x0, y0, x1, y1 in building_boxes)

    placed = 0
    attempts = 0
    while placed < n_trees and attempts < n_trees * 20:
        attempts += 1
        cx = random.uniform(20, MAP_W - 20)
        cz = random.uniform(20, MAP_H - 20)
        if inside_building(cx, cz):
            continue
        placed += 1
        height = random.uniform(8.0, 18.0)
        radius = random.uniform(3.5, 6.5)
        n_foliage = random.randint(200, 450)
        # spherical-ish foliage
        u = np.random.uniform(0, 1, n_foliage)
        v = np.random.uniform(0, 1, n_foliage)
        theta = 2 * np.pi * u
        phi = np.arccos(2 * v - 1)
        fx = cx + radius * np.sin(phi) * np.cos(theta)
        fy = height * 0.6 + (radius * 0.8) * np.sin(phi) * np.sin(theta)
        fz = cz + radius * np.cos(phi)
        # trunk
        n_trunk = 30
        tx = np.random.normal(cx, 0.4, n_trunk)
        tz = np.random.normal(cz, 0.4, n_trunk)
        ty = np.random.uniform(0, height * 0.35, n_trunk)
        all_x = np.concatenate([fx, tx])
        all_y = np.concatenate([fy, ty])
        all_z = np.concatenate([fz, tz])
        n_total = len(all_x)
        foliage_color = np.tile(COLORS["tree"], (n_foliage, 1))
        trunk_color = np.tile(COLORS["trunk"], (n_trunk, 1))
        base = np.vstack([foliage_color, trunk_color])
        cols = np.clip(base.astype(np.int16) + np.random.randint(-10, 11, size=(n_total, 3)), 0, 255).astype(np.uint8)
        for x, y, z, c in zip(all_x, all_y, all_z, cols):
            points.append((float(x), float(y), float(z), int(c[0]), int(c[1]), int(c[2])))


def generate_rocks(points: List[Tuple[float, float, float, int, int, int]], n_rocks: int = 25) -> None:
    """Small rock clusters."""
    for _ in range(n_rocks):
        cx, cz = random.uniform(50, MAP_W - 50), random.uniform(50, MAP_H - 50)
        n = random.randint(30, 80)
        xs = cx + np.random.normal(0, 2, n)
        zs = cz + np.random.normal(0, 2, n)
        ys = np.random.uniform(0, 1.5, n)
        cols = np.tile(COLORS["rock"], (n, 1))
        cols = np.clip(cols.astype(np.int16) + np.random.randint(-8, 9, size=(n, 3)), 0, 255).astype(np.uint8)
        for x, y, z, c in zip(xs, ys, zs, cols):
            points.append((float(x), float(y), float(z), int(c[0]), int(c[1]), int(c[2])))


def write_ply(path: str, points: List[Tuple[float, float, float, int, int, int]]) -> None:
    """Write an ASCII PLY file with vertex colors."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write("ply\n")
        f.write("format ascii 1.0\n")
        f.write(f"element vertex {len(points)}\n")
        f.write("property float x\n")
        f.write("property float y\n")
        f.write("property float z\n")
        f.write("property uchar red\n")
        f.write("property uchar green\n")
        f.write("property uchar blue\n")
        f.write("end_header\n")
        for x, y, z, r, g, b in points:
            f.write(f"{x:.3f} {y:.3f} {z:.3f} {r} {g} {b}\n")


def main() -> None:
    random.seed(42)
    np.random.seed(42)
    points: List[Tuple[float, float, float, int, int, int]] = []

    generate_ground(points, target=12000)
    generate_roads(points, samples_per_unit=0.9)
    # Buildings are rendered as Three.js mesh geometry in 3d.html,
    # not as point-cloud dots, so we skip them here.
    generate_trees(points, n_trees=70)
    generate_rocks(points, n_rocks=30)

    write_ply(OUT_PATH, points)
    print(f"Wrote {len(points):,} points to {OUT_PATH}")


if __name__ == "__main__":
    main()
