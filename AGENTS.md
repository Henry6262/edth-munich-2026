# AGENTS.md — SCOUT / EDTH Munich 2026

> Agent-native development guide. Any AI assistant should read this before modifying code.

---

## Project identity

- **Name:** SCOUT C2
- **Event:** EDTH Munich 2026
- **Challenges:** 01-ats (ATS GmbH) + 01-se3 Track 2 (SE3 Labs)
- **Demo angle:** Tactical C2 / Counter-UAS ground sensor node
- **Hardware:** PiCrawler + Raspberry Pi 5 + Sony IMX500 AI Camera

---

## Agent workflow

1. Read `CLAUDE.md` (this file supersedes parent `AGENTS.md`).
2. Check `README.md` for current status and quick-start commands.
3. Make minimal, testable changes.
4. Run the 01-ats evaluator after any algorithm change.
5. Update this file if conventions change.

---

## Code rules

- **01-ats submission:** only `src/algorithm/explorer.py` is submitted. It may only use Python stdlib + `networkx`.
- **01-se3 submission:** only `side-quests/01-se3-change-detection/change_detector.py`. OpenCV only.
- **Robot code:** runs on Raspberry Pi 5. Avoid heavy dependencies.
- **Telemetry server:** Flask, must work offline.
- **Admin + operator frontends:** static HTML/CSS/JS. Operator app is a single file with no build step.
- **No cloud APIs** in the demo path.

---

## File ownership

| File | Owner | Change policy |
|------|-------|---------------|
| `src/algorithm/explorer.py` | Algorithm dev | Must pass `run_eval.py` |
| `side-quests/01-se3-change-detection/change_detector.py` | CV dev | Must run standalone |
| `src/robot/*.py` | Hardware dev | Test on Pi when possible |
| `src/c2/server.py` | Backend dev | Must run offline |
| `src/c2/simulator.py` | Sim/video dev | Drives frontend without robot |
| `src/c2/video_renderer.py` | Sim/video dev | Outputs demo MP4 |
| `src/admin/index.html` | Frontend dev | Must work on tablet/laptop |
| `src/operator/index.html` | Frontend dev | Must work on phone |
| `docs/PITCH.md` | Pitch lead | Keep under 3 minutes |
| `docs/DEMO_SCRIPT.md` | Demo lead | Update as hardware changes |
| `docs/IMPLEMENTATION_PLAN.md` | Build lead | Update daily |

---

## Testing

```bash
cd challenge/graph_explo
uv run run_eval.py --submission ../../src/algorithm/explorer.py --graphs graphs/train --quiet
```

Target: 100% completion on all training graphs. Lower total score is better.

---

## Communication style

- Be concise.
- Cite file paths, not summaries.
- Do not add features outside scope without team approval.
