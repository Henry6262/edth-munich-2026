# EDTH Munich 2026 — Team Submission

## Team Name

SCOUT by Mashina Robotics

## One-liner

A €200 autonomous ground robot and tactical C2 system for graph exploration, surveillance, and change detection in unknown environments.

## Challenge(s)

- **ATS GmbH:** 01-ats — 3D Graph Exploration & Surveillance
- **SE3 Labs:** 01-se3 Track 2 — Tactical Change Detection

## Details

We are building SCOUT C2: a low-cost autonomous ground reconnaissance system built around a SunFounder PiCrawler quadruped, Raspberry Pi 5, and Raspberry Pi AI Camera.

SCOUT explores unknown environments, detects relevant objects on-device, reports changes between patrol passes, and streams everything into a command dashboard and mobile operator view. The demo combines one physical walking robot with simulated multi-agent coverage, showing how a cheap ground node can become part of a tactical sensing network.

For the hackathon, we are solving two challenges:

### ATS GmbH 01-ats

We built a graph exploration algorithm for unknown environments. SCOUT agents explore a village/mission graph, maximize coverage, and report surveillance progress.

### SE3 Labs 01-se3 Track 2

We built a tactical change-detection pipeline that compares before/after patrol imagery and highlights meaningful changes such as opened doors, moved objects, or new threats.

The product vision is simple: instead of sending humans first into unknown buildings, warehouses, disaster zones, or base perimeters, deploy cheap autonomous ground sensors that patrol, detect, and report back to a human operator.

### Current demo includes

- SunFounder PiCrawler quadruped robot
- Raspberry Pi 5
- Raspberry Pi AI Camera / OpenCV vision
- Mobile operator app
- 3D tactical map
- ATS graph exploration submission
- SE3 change-detection submission

## Links

- **GitHub:** https://github.com/Henry6262/MashinaRobotics.git
- **Product site:** https://mashinarobotics.com
- **Telegram:** web3h3nry

## Progress

MVP in progress. Hardware is assembled and walking. Core C2 demo, mobile operator view, graph exploration algorithm, and change-detection pipeline are implemented locally. We are polishing the final demo flow, challenge submissions, and pitch.

## Team needs

- **Robotics / embedded dev:** Python, Raspberry Pi, servo control, sensor integration
- **Strong Python / CV dev:** OpenCV, algorithms, graph exploration, tactical change detection

DM before joining. Tell me your superpower and confirm you are in Munich for the full 42 hours.
