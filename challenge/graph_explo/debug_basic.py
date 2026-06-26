"""Debug basic graph surveillance."""

import sys
sys.path.insert(0, "../..")

from exploration_challenge.evaluator import run_suite
from exploration_challenge.graph_io import load_graph
from run_eval import load_explorer_class

world = load_graph("graphs/train/basic.json")
Explorer, _, _ = load_explorer_class("../../src/algorithm/explorer.py")

class DebugExplorer(Explorer):
    def step(self, observations, phase):
        actions = super().step(observations, phase)
        if phase == "surveil" and self.stall_count > 0:
            print(f"stall={self.stall_count} pos={[o.position for o in observations]} targets={self.targets} route_idx={self._route_idx} route_lens={[len(r) for r in (self._surveil_routes or [])]}")
        return actions

result = run_suite(worlds=[world], make_explorer=DebugExplorer, seeds=[0], n_agents=3, max_steps=200, live=True)
print(result)
