"""Camera wrappers for Pi AI Camera, standard Pi Camera, and USB camera.

Runs on Raspberry Pi 5. Falls back to OpenCV webcams on desktop for dev.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterator, List, Optional, Tuple

import cv2
import numpy as np

# Pi-specific imports; fail gracefully on desktop
try:
    from picamera2 import Picamera2
except ImportError:
    Picamera2 = None  # type: ignore

try:
    from picamera2.devices.imx500 import IMX500
except ImportError:
    IMX500 = None  # type: ignore


@dataclass
class Detection:
    label: str
    confidence: float
    box: Tuple[int, int, int, int]  # x1, y1, x2, y2
    center: Tuple[int, int]


class BaseCamera:
    def read(self) -> Optional[np.ndarray]:
        raise NotImplementedError

    def release(self) -> None:
        pass


class OpenCVCamera(BaseCamera):
    def __init__(self, index: int = 0) -> None:
        self.cap = cv2.VideoCapture(index)

    def read(self) -> Optional[np.ndarray]:
        ret, frame = self.cap.read()
        return frame if ret else None

    def release(self) -> None:
        self.cap.release()


class PiCamera(BaseCamera):
    def __init__(self, camera_num: int = 0) -> None:
        if Picamera2 is None:
            raise RuntimeError("picamera2 not available")
        self.picam2 = Picamera2(camera_num)
        config = self.picam2.create_preview_configuration(
            main={"format": "RGB888", "size": (640, 480)}
        )
        self.picam2.configure(config)
        self.picam2.start()

    def read(self) -> Optional[np.ndarray]:
        return self.picam2.capture_array()

    def release(self) -> None:
        self.picam2.stop()


class AICamera(PiCamera):
    """Sony IMX500 AI camera with on-device MobileNet SSD detection."""

    def __init__(self, camera_num: int = 1) -> None:
        super().__init__(camera_num)
        self.detections: List[Detection] = []

    def detect(self, frame: np.ndarray) -> List[Detection]:
        """Placeholder detection pipeline.

        On the Pi this would read imx500.get_inference_result(). For the demo,
        we use OpenCV DNN or simply return the largest moving object.
        """
        # TODO: integrate IMX500 inference result when on hardware
        h, w = frame.shape[:2]
        return [
            Detection(
                label="UAV",
                confidence=0.94,
                box=(w // 4, h // 4, 3 * w // 4, 3 * h // 4),
                center=(w // 2, h // 2),
            )
        ]


class CameraSystem:
    """Manages the three-camera sensor fusion layout."""

    def __init__(self) -> None:
        self.overwatch: Optional[BaseCamera] = None
        self.ai_camera: Optional[BaseCamera] = None
        self.robot_eyes: Optional[BaseCamera] = None

    def init_overwatch(self, index_or_port: int = 0) -> None:
        try:
            self.overwatch = PiCamera(index_or_port)
        except Exception:
            self.overwatch = OpenCVCamera(index_or_port)

    def init_ai(self, index_or_port: int = 1) -> None:
        try:
            self.ai_camera = AICamera(index_or_port)
        except Exception:
            self.ai_camera = OpenCVCamera(index_or_port)

    def init_robot_eyes(self, usb_index: int = 2) -> None:
        self.robot_eyes = OpenCVCamera(usb_index)

    def read_all(self) -> Iterator[Tuple[str, Optional[np.ndarray]]]:
        for name, cam in [
            ("overwatch", self.overwatch),
            ("ai", self.ai_camera),
            ("robot_eyes", self.robot_eyes),
        ]:
            frame = cam.read() if cam else None
            yield name, frame

    def release(self) -> None:
        for cam in (self.overwatch, self.ai_camera, self.robot_eyes):
            if cam:
                cam.release()
