"""Build a 3D surface mesh from Alex's SE3 point cloud for the 3D view.

Usage:
    cd edth-munich-2026
    source .venv/bin/activate
    python scripts/mesh_from_point_cloud.py

Outputs:
    - side-quests/01-se3-change-detection/data/point_cloud_mesh.ply
    - side-quests/01-se3-change-detection/data/point_cloud_mesh_preview.png
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from plyfile import PlyData, PlyElement
from scipy.spatial import Delaunay

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "side-quests" / "01-se3-change-detection" / "data"
OUT_DIR.mkdir(parents=True, exist_ok=True)

PLY_PATH = "/Users/henry/Downloads/point_cloud.ply"

# Region of interest: the compound-like area seen in the full preview.
X_MIN, X_MAX = 717150.0, 717300.0
Y_MIN, Y_MAX = 5355640.0, 5355740.0
MAX_VERTS = 12000
MAX_EDGE = 2.0  # meters; drop triangles spanning gaps


def load_ply(path: str):
    ply = PlyData.read(path)
    v = ply["vertex"].data
    pts = np.column_stack([v["x"], v["y"], v["z"]]).astype(np.float32)
    colors = np.column_stack([v["red"], v["green"], v["blue"]]).astype(np.uint8)
    return pts, colors


def crop(pts: np.ndarray, colors: np.ndarray):
    mask = (
        (pts[:, 0] >= X_MIN)
        & (pts[:, 0] <= X_MAX)
        & (pts[:, 1] >= Y_MIN)
        & (pts[:, 1] <= Y_MAX)
    )
    return pts[mask], colors[mask]


def downsample_to(pts: np.ndarray, colors: np.ndarray, n: int):
    if len(pts) <= n:
        return pts, colors
    idx = np.random.choice(len(pts), n, replace=False)
    return pts[idx], colors[idx]


def build_mesh(pts: np.ndarray, colors: np.ndarray):
    # Center horizontally around origin; keep z as height.
    center_xy = pts[:, :2].mean(axis=0)
    centered = pts.copy()
    centered[:, 0] -= center_xy[0]
    centered[:, 1] -= center_xy[1]

    tri = Delaunay(centered[:, :2])
    verts = centered
    faces = []
    for simplex in tri.simplices:
        a, b, c = simplex
        # Skip long-edge triangles (gaps / border artifacts).
        e1 = np.linalg.norm(verts[a, :2] - verts[b, :2])
        e2 = np.linalg.norm(verts[b, :2] - verts[c, :2])
        e3 = np.linalg.norm(verts[c, :2] - verts[a, :2])
        if e1 < MAX_EDGE and e2 < MAX_EDGE and e3 < MAX_EDGE:
            faces.append([a, b, c])
    return verts, colors, np.array(faces, dtype=np.int32)


def write_mesh_ply(path: Path, verts: np.ndarray, colors: np.ndarray, faces: np.ndarray):
    # Vertex record.
    vrec = np.core.records.fromarrays(
        [verts[:, 0], verts[:, 1], verts[:, 2], colors[:, 0], colors[:, 1], colors[:, 2]],
        dtype=[("x", "f4"), ("y", "f4"), ("z", "f4"), ("red", "u1"), ("green", "u1"), ("blue", "u1")],
    )
    # Face record: list of vertex indices per triangle.
    freclist = []
    for f in faces:
        freclist.append(([f[0], f[1], f[2]],))
    frectype = np.dtype([("vertex_indices", "i4", (3,))])
    frec = np.array(freclist, dtype=frectype)
    elv = PlyElement.describe(vrec, "vertex")
    elf = PlyElement.describe(frec, "face")
    PlyData([elv, elf], text=True).write(str(path))


def render_preview(verts: np.ndarray, colors: np.ndarray, faces: np.ndarray, path: Path):
    fig = plt.figure(figsize=(12, 10))
    ax = fig.add_subplot(111, projection="3d")
    # Sample faces for speed.
    n = len(faces)
    step = max(1, n // 15000)
    f = faces[::step]
    # Triangulate vertices for plotting.
    xs = verts[f, 0]
    ys = verts[f, 1]
    zs = verts[f, 2]
    cs = colors[f] / 255.0
    ax.plot_trisurf(
        verts[:, 0], verts[:, 1], verts[:, 2],
        triangles=f,
        color="gray",
        alpha=0.8,
    )
    ax.set_title(f"SE3 mesh ({len(faces):,} triangles)")
    ax.set_xlabel("x"); ax.set_ylabel("y"); ax.set_zlabel("z")
    plt.savefig(path, dpi=150)
    plt.close(fig)


def main():
    print("Loading point cloud...")
    pts, colors = load_ply(PLY_PATH)
    print(f"  total points: {len(pts):,}")
    pts, colors = crop(pts, colors)
    print(f"  cropped points: {len(pts):,}")
    pts, colors = downsample_to(pts, colors, MAX_VERTS)
    print(f"  sampled points: {len(pts):,}")

    verts, colors, faces = build_mesh(pts, colors)
    print(f"  mesh: {len(verts):,} vertices, {len(faces):,} triangles")

    out_ply = OUT_DIR / "point_cloud_mesh.ply"
    write_mesh_ply(out_ply, verts, colors, faces)
    print(f"Saved mesh: {out_ply}")

    preview = OUT_DIR / "point_cloud_mesh_preview.png"
    render_preview(verts, colors, faces, preview)
    print(f"Saved preview: {preview}")


if __name__ == "__main__":
    main()
