"""Tactical change detection for EDTH 01-se3 Track 2.

Detects tactically relevant changes between two images while filtering noise
from lighting, shadows, and small movements.

Usage:
    python change_detector.py before.jpg after.jpg output.jpg
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from typing import List, Optional, Tuple

import cv2
import numpy as np


@dataclass
class Change:
    x: int
    y: int
    w: int
    h: int
    area: int
    significance: str  # HIGH, MEDIUM, LOW
    change_type: str   # ADDED, REMOVED, REPLACED
    confidence: float


class TacticalChangeDetector:
    """Detect tactically relevant changes between two images."""

    def __init__(
        self,
        min_area: int = 500,
        high_threshold: float = 0.05,
        medium_threshold: float = 0.01,
        low_threshold: float = 0.005,
        orb_features: int = 5000,
    ) -> None:
        self.min_area = min_area
        self.high_threshold = high_threshold
        self.medium_threshold = medium_threshold
        self.low_threshold = low_threshold
        self.orb_features = orb_features

    def detect(self, before: np.ndarray, after: np.ndarray) -> List[Change]:
        """Return list of detected changes."""
        aligned = self._align(before, after)
        if aligned is None:
            # Fallback: compare without alignment
            aligned = after

        diff = self._compute_diff(before, aligned)
        mask = self._threshold_and_clean(diff)
        changes = self._extract_changes(before, aligned, mask)
        return changes

    def visualize(
        self,
        before: np.ndarray,
        after: np.ndarray,
        changes: List[Change],
    ) -> np.ndarray:
        """Create side-by-side visualization with change overlays."""
        h, w = before.shape[:2]
        canvas = np.zeros((h, w * 2, 3), dtype=np.uint8)
        canvas[:, :w] = before
        canvas[:, w:] = after

        for change in changes:
            color = {
                "HIGH": (0, 0, 255),
                "MEDIUM": (0, 165, 255),
                "LOW": (0, 255, 0),
            }.get(change.significance, (255, 255, 255))
            cv2.rectangle(canvas, (change.x, change.y), (change.x + change.w, change.y + change.h), color, 2)
            cv2.rectangle(
                canvas,
                (change.x + w, change.y),
                (change.x + w + change.w, change.y + change.h),
                color,
                2,
            )
            label = f"{change.change_type} {change.significance}"
            cv2.putText(
                canvas,
                label,
                (change.x, max(0, change.y - 5)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                color,
                1,
            )

        # Legend
        cv2.putText(
            canvas,
            f"Changes: {len(changes)}",
            (10, 20),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (255, 255, 255),
            2,
        )
        return canvas

    def _align(self, before: np.ndarray, after: np.ndarray) -> Optional[np.ndarray]:
        """Align after image to before using ORB + RANSAC homography."""
        gray_before = cv2.cvtColor(before, cv2.COLOR_BGR2GRAY)
        gray_after = cv2.cvtColor(after, cv2.COLOR_BGR2GRAY)

        orb = cv2.ORB_create(nfeatures=self.orb_features)
        kp1, des1 = orb.detectAndCompute(gray_before, None)
        kp2, des2 = orb.detectAndCompute(gray_after, None)

        if des1 is None or des2 is None or len(kp1) < 4 or len(kp2) < 4:
            return None

        matcher = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
        matches = matcher.match(des1, des2)
        if len(matches) < 10:
            return None

        matches = sorted(matches, key=lambda x: x.distance)[: min(len(matches), 200)]
        src_pts = np.float32([kp1[m.queryIdx].pt for m in matches]).reshape(-1, 1, 2)
        dst_pts = np.float32([kp2[m.trainIdx].pt for m in matches]).reshape(-1, 1, 2)

        H, mask = cv2.findHomography(dst_pts, src_pts, cv2.RANSAC, 5.0)
        if H is None:
            return None

        h, w = before.shape[:2]
        aligned = cv2.warpPerspective(after, H, (w, h))
        return aligned

    def _compute_diff(self, before: np.ndarray, after: np.ndarray) -> np.ndarray:
        """Compute pixel-wise difference robust to small misalignment."""
        gray_before = cv2.cvtColor(before, cv2.COLOR_BGR2GRAY)
        gray_after = cv2.cvtColor(after, cv2.COLOR_BGR2GRAY)
        diff = cv2.absdiff(gray_before, gray_after)
        # Blur to reduce noise from small shifts
        diff = cv2.GaussianBlur(diff, (5, 5), 0)
        return diff

    def _threshold_and_clean(self, diff: np.ndarray) -> np.ndarray:
        """Otsu threshold + morphological cleanup."""
        _, mask = cv2.threshold(diff, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
        return mask

    def _extract_changes(
        self,
        before: np.ndarray,
        after: np.ndarray,
        mask: np.ndarray,
    ) -> List[Change]:
        """Extract change regions from mask and classify them."""
        num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(mask, 8)
        h, w = before.shape[:2]
        total_area = h * w
        changes = []

        for i in range(1, num_labels):
            x, y, bw, bh, area = stats[i]
            if area < self.min_area:
                continue

            region_mask = (labels == i).astype(np.uint8) * 255
            before_mean = cv2.mean(before, mask=region_mask)[:3]
            after_mean = cv2.mean(after, mask=region_mask)[:3]
            color_shift = sum(abs(a - b) for a, b in zip(before_mean, after_mean)) / 3.0

            if color_shift > 80:
                change_type = "REPLACED"
            elif after_mean[0] + after_mean[1] + after_mean[2] > before_mean[0] + before_mean[1] + before_mean[2]:
                change_type = "ADDED"
            else:
                change_type = "REMOVED"

            area_ratio = area / total_area
            if area_ratio > self.high_threshold:
                significance = "HIGH"
            elif area_ratio > self.medium_threshold:
                significance = "MEDIUM"
            elif area_ratio > self.low_threshold:
                significance = "LOW"
            else:
                continue

            changes.append(
                Change(
                    x=int(x),
                    y=int(y),
                    w=int(bw),
                    h=int(bh),
                    area=int(area),
                    significance=significance,
                    change_type=change_type,
                    confidence=min(1.0, area_ratio / self.high_threshold),
                )
            )

        # Sort by significance and area
        significance_order = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
        changes.sort(key=lambda c: (significance_order.get(c.significance, 3), -c.area))
        return changes


def main() -> None:
    parser = argparse.ArgumentParser(description="Tactical change detection")
    parser.add_argument("before", help="Before image path")
    parser.add_argument("after", help="After image path")
    parser.add_argument("output", help="Output visualization path")
    parser.add_argument("--min-area", type=int, default=500)
    args = parser.parse_args()

    before = cv2.imread(args.before)
    after = cv2.imread(args.after)
    if before is None or after is None:
        raise ValueError("Could not load input images")

    detector = TacticalChangeDetector(min_area=args.min_area)
    changes = detector.detect(before, after)
    vis = detector.visualize(before, after, changes)
    cv2.imwrite(args.output, vis)

    print(f"Detected {len(changes)} changes:")
    for c in changes:
        print(f"  {c.significance:6} {c.change_type:9} area={c.area:5} conf={c.confidence:.2f}")


if __name__ == "__main__":
    main()
