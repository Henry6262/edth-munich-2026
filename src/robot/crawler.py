"""PiCrawler movement wrapper.

This module runs on the Raspberry Pi and abstracts the SunFounder picrawler
library so the demo code doesn't depend on exact servo details.
"""

from __future__ import annotations

import time
from enum import Enum
from typing import Optional

# The picrawler library is only available on the Pi; provide a desktop stub.
try:
    from picrawler import Picrawler
except ImportError:
    Picrawler = None  # type: ignore


class Direction(str, Enum):
    FORWARD = "forward"
    BACKWARD = "backward"
    LEFT = "left"
    RIGHT = "right"


class Crawler:
    """High-level interface to the PiCrawler quadruped."""

    def __init__(self) -> None:
        self._crawler = Picrawler() if Picrawler else None
        self.speed = 60
        self.step_length = 25  # mm per step

    def ready(self) -> bool:
        return self._crawler is not None

    def calibrate(self) -> None:
        """Run servo calibration. Robot must be standing in neutral pose."""
        if self._crawler:
            self._crawler.calibration()

    def stand(self) -> None:
        if self._crawler:
            self._crawler.do_action("stand", speed=self.speed)
            time.sleep(0.5)

    def stop(self) -> None:
        if self._crawler:
            self._crawler.do_action("stand", speed=self.speed)

    def step(self, direction: Direction, steps: int = 1) -> None:
        """Move a number of steps in the given direction."""
        if not self._crawler:
            print(f"[Crawler stub] step {direction} x{steps}")
            return

        action_map = {
            Direction.FORWARD: "forward",
            Direction.BACKWARD: "backward",
            Direction.LEFT: "turn left",
            Direction.RIGHT: "turn right",
        }
        action = action_map[direction]
        for _ in range(steps):
            self._crawler.do_action(action, 1, self.speed)
            time.sleep(0.15)

    def turn_toward(self, x_offset: float, frame_width: int) -> None:
        """Turn proportionally to keep a target centered in the camera frame.

        x_offset: horizontal pixel distance from frame center.
        frame_width: camera frame width in pixels.
        """
        if frame_width == 0:
            return
        ratio = x_offset / (frame_width / 2)
        if abs(ratio) < 0.15:
            return  # already centered
        direction = Direction.RIGHT if ratio > 0 else Direction.LEFT
        steps = max(1, min(3, int(abs(ratio) * 3)))
        self.step(direction, steps)

    def shutdown(self) -> None:
        self.stop()
