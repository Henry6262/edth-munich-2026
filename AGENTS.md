# AGENTS.md — SCOUT / EDTH Munich 2026

> Agent-native development guide. Any AI assistant (Claude, Codex, Gemini, etc.) should read this before modifying code.

## Project identity

- **Name:** SCOUT
- **Event:** EDTH Munich 2026
- **Challenge:** 01-ats — 3D Graph Exploration & Surveillance
- **Demo angle:** Autonomous Counter-UAS ground sensor node
- **Hardware:** PiCrawler + Raspberry Pi 5 + Sony IMX500 AI Camera

## Agent workflow

1. Read `CLAUDE.md` (this file supersedes parent `AGENTS.md`).
2. Check `README.md` for current status and quick-start commands.
3. Make minimal, testable changes.
4. Run the challenge evaluator after any algorithm change.
5. Update this file if conventions change.

## Code rules

- **Challenge submission:** only `src/algorithm/explorer.py` is submitted. It may only use Python stdlib + `networkx`.
- **Robot code:** runs on Raspberry Pi 5. Avoid heavy dependencies.
- **Dashboard:** Streamlit, must work offline.
- **No cloud APIs** in the demo path.
- **No mobile app / soldier shared state** in scope. Pitch as future work only.

## File ownership

| File | Owner | Change policy |
|------|-------|---------------|
| `src/algorithm/explorer.py` | Algorithm dev | Must pass `run_eval.py` |
| `src/robot/*.py` | Hardware dev | Test on Pi when possible |
| `src/dashboard/app.py` | Frontend dev | Must run offline |
| `docs/PITCH.md` | Pitch lead | Keep under 3 minutes |
| `docs/DEMO_SCRIPT.md` | Demo lead | Update as hardware changes |

## Testing

```bash
cd challenge/graph_explo
uv run run_eval.py --submission ../../src/algorithm/explorer.py --graphs graphs/train --quiet
```

Target: 100% completion on all training graphs. Lower total score is better.

## Communication style

- Be concise.
- Cite file paths, not summaries.
- Do not add features outside scope without team approval.
