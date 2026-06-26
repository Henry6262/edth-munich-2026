"""Debug script to diagnose Explorer stalls."""

import sys
import traceback

sys.path.insert(0, "../..")

from exploration_challenge.evaluator import _resolve_starts
from exploration_challenge.graph_io import load_graph
from exploration_challenge.simulator import Simulator
from exploration_challenge._internal.config import eval_params
from exploration_challenge._internal.seeding import sensor_seed
from run_eval import load_explorer_class

graph_file = "double_room"
world = load_graph(f"graphs/train/{graph_file}.json")
Explorer, source, path = load_explorer_class("../../src/algorithm/explorer.py")

params = eval_params()
seed = 0
n_agents = 3
k = params["k"]
max_turn_deg = params["max_turn_deg"]
drop_prob = params["drop_prob"]
max_steps = 1000

starts = _resolve_starts(world, seed, None, n_agents)
print(f"starts={starts} n={world.number_of_nodes()}")
sim = Simulator(world, starts=starts, k=k, max_turn_deg=max_turn_deg, drop_prob=drop_prob, seed=sensor_seed(seed))
explorer = Explorer(sensor_k=k)
observations = [sim.observe(i) for i in range(n_agents)]
explorer.reset(starts, observations, seed)

stall = 0
for step in range(max_steps):
    observations = [sim.observe(i) for i in range(n_agents)]
    try:
        actions = explorer.step(observations, sim.phase)
    except Exception:
        traceback.print_exc()
        break
    next_hops = {agent_id: sim.resolve_action(agent_id, action) for agent_id, action in enumerate(actions)}
    moved = sim.step_agents(next_hops)
    sim.steps += 1

    if not any(moved.values()):
        stall += 1
    else:
        stall = 0

    if step % 50 == 0 or (sim.phase == "surveil" and (step % 25 == 0 or (stall > 0 and step % 5 == 0))):
        print(f"step={step} pos={[sim.agents[i].position for i in range(n_agents)]} moved={moved} observed={sim.observed_fraction():.3f} surveilled={sim.surveil_fraction():.3f} phase={sim.phase} targets={explorer.targets}")
    if stall >= 5:
        print(f"STALL at step {step}")
        break
    if sim.is_done():
        print(f"DONE at step {step}")
        break
print(f"FINAL step={step} observed={sim.observed_fraction():.3f} surveilled={sim.surveil_fraction():.3f}")
