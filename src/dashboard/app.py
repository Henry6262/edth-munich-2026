"""Streamlit tactical dashboard for the SCOUT physical demo.

Displays:
- Three camera feeds (overwatch, AI targeting, robot verification)
- Patrol state and sector status
- Threat log and detection confidence
- A simple 2D tactical map
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Dict, List, Optional

import numpy as np

# Streamlit may not be installed on desktop; allow import failure for tests.
try:
    import streamlit as st
except ImportError:
    st = None  # type: ignore


@dataclass
class Threat:
    timestamp: str
    sector: str
    label: str
    confidence: float
    action: str


class Dashboard:
    """Stateful dashboard that can be updated frame-by-frame."""

    def __init__(self) -> None:
        self.state = "PATROL"
        self.sector = "Sector 1"
        self.threats: List[Threat] = []
        self.frames: Dict[str, Optional[np.ndarray]] = {
            "overwatch": None,
            "ai": None,
            "robot_eyes": None,
        }

    def update_frame(self, name: str, frame: Optional[np.ndarray]) -> None:
        self.frames[name] = frame

    def set_state(self, state: str, sector: str = "") -> None:
        self.state = state
        if sector:
            self.sector = sector

    def log_threat(self, threat: Threat) -> None:
        self.threats.insert(0, threat)
        self.threats = self.threats[:20]  # keep last 20

    def render(self) -> None:
        if st is None:
            return

        st.title("SCOUT — Counter-UAS Ground Sensor Node")
        st.markdown(f"### Status: `{self.state}` | {self.sector}")

        col1, col2, col3 = st.columns(3)
        with col1:
            st.subheader("OVERWATCH")
            self._show_frame("overwatch", "Sector CLEAR")
        with col2:
            st.subheader("AI TARGETING")
            self._show_frame("ai", "Scanning...")
        with col3:
            st.subheader("ROBOT VERIFICATION")
            self._show_frame("robot_eyes", "PID: STANDBY")

        st.divider()
        st.subheader("THREAT LOG")
        if not self.threats:
            st.info("No threats detected.")
        for t in self.threats:
            st.markdown(
                f"`{t.timestamp}` **{t.sector}** — {t.label} "
                f"({t.confidence:.0%}) → *{t.action}*"
            )

        st.divider()
        st.caption("Built at EDTH Munich 2026 | SCOUT team")

    def _show_frame(self, name: str, fallback: str) -> None:
        if st is None:
            return
        frame = self.frames.get(name)
        if frame is not None:
            st.image(frame, channels="BGR" if frame.ndim == 3 else "GRAY", use_container_width=True)
        else:
            st.text(fallback)


def main() -> None:
    """Standalone dashboard demo with synthetic frames."""
    if st is None:
        print("Streamlit not installed. Run: pip install streamlit")
        return

    dashboard = Dashboard()
    placeholder = st.empty()

    for i in range(100):
        dashboard.set_state("PATROL", f"Sector {(i % 3) + 1}")
        # Synthetic frames
        for name in dashboard.frames:
            frame = np.random.randint(0, 255, (240, 320, 3), dtype=np.uint8)
            dashboard.update_frame(name, frame)
        if i % 20 == 0:
            dashboard.log_threat(
                Threat(
                    timestamp=time.strftime("%H:%M:%S"),
                    sector=dashboard.sector,
                    label="UAV",
                    confidence=0.94,
                    action="TRACKING",
                )
            )
        with placeholder.container():
            dashboard.render()
        time.sleep(0.5)


if __name__ == "__main__":
    main()
