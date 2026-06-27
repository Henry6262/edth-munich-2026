"""Inspect and downsample Alex's SE3 point cloud without Open3D.

Usage:
    cd edth-munich-2026
    source .venv/bin/activate
    python scripts/inspect_point_cloud.py /Users/henry/Downloads/point_cloud.ply

Outputs:
    - side-quests/01-se3-change-detection/data/point_cloud_downsampled.ply
    - side-quests/01-se3-change-detection/data/point_cloud_preview.png
"""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from plyfile import PlyData, PlyElement

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "side-quests" / "01-se3-change-detection" / "data"
OUT_DIR.mkdir(parents=True, exist_ok=True)


def load_ply(path: str):
    ply = PlyData.read(path)
    v = ply["vertex"].data
    pts = np.column_stack([v["x"], v["y"], v["z"]]).astype(np.float32)
    colors = (
        np.column_stack([v["red"], v["green"], v["blue"]]).astype(np.uint8)
        if {"red", "green", "blue"} <= set(v.dtype.names)
        else None
    )
    return pts, colors


def voxel_downsample(pts: np.ndarray, colors: np.ndarray | None, voxel_size: float):
    centered = pts - pts.mean(axis=0)
    keys = np.floor(centered / voxel_size).astype(np.int32)
    # unique voxel keys, keep first point per voxel
    dfmt = [("x", np.float32), ("y", np.float32), ("z", np.float32)]
    if colors is not None:
        dfmt += [("red", np.uint8), ("green", np.uint8), ("blue", np.uint8)]
    packed = np.core.records.fromarrays(
        [keys[:, 0], keys[:, 1], keys[:, 2]], names=["kx", "ky", "kz"]
    )
    _, idx = np.unique(packed, return_index=True)
    ds_pts = centered[idx]
    ds_colors = colors[idx] if colors is not None else None
    return ds_pts, ds_colors


def write_ply(path: Path, pts: np.ndarray, colors: np.ndarray | None) -> None:
    dfmt = [("x", "f4"), ("y", "f4"), ("z", "f4")]
    arr = [pts[:, 0], pts[:, 1], pts[:, 2]]
    if colors is not None:
        dfmt += [("red", "u1"), ("green", "u1"), ("blue", "u1")]
        arr += [colors[:, 0], colors[:, 1], colors[:, 2]]
    vertex = np.core.records.fromarrays(arr, dtype=dfmt)
    el = PlyElement.describe(vertex, "vertex")
    PlyData([el], text=True).write(str(path))


def render_preview(pts: np.ndarray, colors: np.ndarray | None, path: Path) -> None:
    fig, ax = plt.subplots(figsize=(12, 9))
    # Plot at most 150k points for speed.
    n = len(pts)
    step = max(1, n // 150000)
    p = pts[::step]
    c = colors[::step] / 255.0 if colors is not None else None
    ax.scatter(p[:, 0], p[:, 1], c=c, s=0.1, alpha=0.6)
    ax.set_aspect("equal")
    ax.set_title(f"SE3 point cloud (top-down) — {n:,} pts downsampled")
    ax.set_xlabel("x (m)")
    ax.set_ylabel("y (m)")
    plt.tight_layout()
    plt.savefig(path, dpi=150)
    plt.close(fig)


def main(ply_path: str) -> None:
    print(f"Loading {ply_path} ...")
    pts, colors = load_ply(ply_path)
    print(f"  points: {len(pts):,}")
    min_b, max_b = pts.min(axis=0), pts.max(axis=0)
    print(f"  bounds: {min_b} -> {max_b}")
    print(f"  size (m): {max_b - min_b}")
    print(f"  center: {(min_b + max_b) / 2}")
    print(f"  has colors: {colors is not None}")

    voxel_size = 0.5  # meters
    print(f"Downsampling with voxel size {voxel_size} m ...")
    ds_pts, ds_colors = voxel_downsample(pts, colors, voxel_size)
    print(f"  downsampled points: {len(ds_pts):,}")

    out_ply = OUT_DIR / "point_cloud_downsampled.ply"
    write_ply(out_ply, ds_pts, ds_colors)
    print(f"Saved: {out_ply}")

    preview = OUT_DIR / "point_cloud_preview.png"
    render_preview(ds_pts, ds_colors, preview)
    print(f"Saved preview: {preview}")


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else "/Users/henry/Downloads/point_cloud.ply"
    main(path)
