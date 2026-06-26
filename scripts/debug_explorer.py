"""Debug script to get full traceback from Explorer failures."""

import sys
import traceback

sys.path.insert(0, "challenge/graph_explo")

from exploration_challenge.evaluator import run_suite
from exploration_challenge.graph_io import load_graph
from run_eval import load_explorer_class

graphs = ["challenge/graph_explo/graphs/train/obstacles.json"]
Explorer, source, path = load_explorer_class("src/algorithm/explorer.py")

try:
    result = run_suite(
        graph_paths=graphs,
        explorer_cls=Explorer,
        eval_params={
            "k": 4,
            "max_turn_deg": 75.0,
            "drop_prob": 0.0,
            "n_agents": 1,
            "seeds": [0],
            "max_steps": 1000,
            "explore_threshold": 0.9,
            "surveil_threshold": 0.9,
        },
        step_delay=0.0,
    )
    print(result)
except Exception:
    traceback.print_exc()
