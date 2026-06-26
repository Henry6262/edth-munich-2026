"""Check k-hop coverage sizes in train_s0."""

import sys
sys.path.insert(0, "../..")

from exploration_challenge.graph_io import load_graph

world = load_graph("graphs/train/double_room.json")
print(f"nodes={world.number_of_nodes()} edges={world.number_of_edges()}")

# Check average degree
avg_degree = sum(dict(world.degree()).values()) / world.number_of_nodes()
print(f"avg degree={avg_degree:.2f}")

# Check k-hop ball sizes for a few random nodes
import random
random.seed(0)
for k in [1, 2, 3, 4]:
    sizes = []
    for _ in range(20):
        start = random.choice(list(world.nodes()))
        seen = {start}
        frontier = {start}
        for _ in range(k):
            nxt = set()
            for n in frontier:
                nxt.update(world.neighbors(n))
            nxt -= seen
            seen.update(nxt)
            frontier = nxt
        sizes.append(len(seen))
    print(f"k={k}: avg ball size={sum(sizes)/len(sizes):.1f} min={min(sizes)} max={max(sizes)}")
