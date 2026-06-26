# 01-se3 Track 2 — Tactical Change Detection

Side quest for EDTH Munich 2026. Detect tactically relevant changes between two patrol photos.

## Algorithm

1. **Align** images with ORB features + RANSAC homography
2. **Diff** aligned images with `cv2.absdiff`
3. **Threshold** with Otsu's method
4. **Clean** noise with morphological open/close
5. **Extract** connected components
6. **Classify** by area and color shift:
   - `ADDED` — brighter region
   - `REMOVED` — darker region
   - `REPLACED` — color shifted

## Usage

```bash
pip install -r requirements.txt
python change_detector.py before.jpg after.jpg output.jpg
```

## Robot Demo Integration

- Pass 1: robot takes photo of each sector → `before_{node}.jpg`
- Pass 2: robot takes photo again → `after_{node}.jpg`
- Run detector on each pair
- Display side-by-side with overlays on dashboard

## Evaluation

SE3 Labs evaluates on hold-out test images. Key metrics:
- Detection accuracy
- False positive rate
- Tactical relevance of reported changes
