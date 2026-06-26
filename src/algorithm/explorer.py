"""SCOUT submission for EDTH 01-ats: 3D Graph Exploration & Surveillance.

Implements a centralized multi-UAV Explorer that builds a persistent map from
depth-limited observations, plans shortest paths on the discovered graph, and
coordinates three agents through explore and surveil phases.

Usage with the challenge evaluator:
    cd challenge/graph_explo
    uv run run_eval.py --submission ../../src/algorithm/explorer.py \
        --graphs graphs/train --quiet

Only stdlib + networkx are used so this file is a valid single-file submission.
"""

from __future__ import annotations

import heapq
import math
import random
from collections import defaultdict
from typing import Dict, List, Optional, Set, Tuple

import networkx as nx

# The evaluator injects the parent directory so the Observation import works
# when this file is loaded as a submission. Guard against standalone import.
try:
    from exploration_challenge.observation import Observation
except ImportError:  # pragma: no cover - fallback for local dev outside eval
    Observation = object  # type: ignore


class _Map:
    """Persistent map built from merging all UAV observations."""

    def __init__(self) -> None:
        self.graph = nx.Graph()
        self.observed: Set[int] = set()
        self.visited: Set[int] = set()
        self.positions: Dict[int, Tuple[float, float, float]] = {}

    def merge(self, observations: List[Observation]) -> None:
        for obs in observations:
            self.observed.update(n.id for n in obs.nodes)
            self.visited.update(obs.visited)
            self.visited.add(obs.position)
            self.positions[obs.position] = obs.position_xyz
            for n in obs.nodes:
                self.positions[n.id] = (n.x, n.y, n.z)
                if not self.graph.has_node(n.id):
                    self.graph.add_node(n.id, pos=(n.x, n.y, n.z))
            for e in obs.edges:
                if not self.graph.has_edge(e.u, e.v):
                    self.graph.add_edge(e.u, e.v, weight=e.cost)

    def has_node(self, node_id: int) -> bool:
        return self.graph.has_node(node_id)

    def neighbors(self, node_id: int) -> List[int]:
        return list(self.graph.neighbors(node_id))

    def shortest_path(self, source: int, target: int) -> List[int]:
        """Return node path source → target on known graph, or [] if unreachable."""
        if source == target:
            return [source]
        try:
            return nx.shortest_path(self.graph, source, target, weight="weight")
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            return []

    def path_cost(self, path: List[int]) -> float:
        cost = 0.0
        for u, v in zip(path, path[1:]):
            data = self.graph.get_edge_data(u, v)
            cost += data.get("weight", math.dist(self.positions[u], self.positions[v]))
        return cost


class Explorer:
    """Centralized policy for 3 UAVs."""

    def __init__(self) -> None:
        self.map = _Map()
        self.rng = random.Random(0)
        self.n_agents = 3
        self.positions: List[int] = []
        self.targets: List[Optional[int]] = [None, None, None]
        self.paths: List[List[int]] = [[], [], []]
        # Coverage tracking
        self.explore_seen: Set[int] = set()
        self.surveil_seen: Set[int] = set()
        # For tie-breaking and stall detection
        self.last_positions: Optional[List[int]] = None
        self.stall_count = 0

    def reset(
        self,
        starts: List[int],
        observations: List[Observation],
        seed: Optional[int] = None,
    ) -> None:
        self.rng = random.Random(seed)
        self.map = _Map()
        self.map.merge(observations)
        self.positions = list(starts)
        self.targets = [None] * self.n_agents
        self.paths = [[] for _ in range(self.n_agents)]
        self.explore_seen: Set[int] = set()
        self.surveil_seen: Set[int] = set()
        self.last_positions = None
        self.stall_count = 0
        for obs in observations:
            self.explore_seen.update(n.id for n in obs.nodes)

    def step(self, observations: List[Observation], phase: str) -> List[int]:
        self.map.merge(observations)
        self.positions = [obs.position for obs in observations]

        # Update coverage counters
        for obs in observations:
            if phase == "explore":
                self.explore_seen.update(n.id for n in obs.nodes)
            else:
                self.surveil_seen.update(n.id for n in obs.nodes)

        # Detect stall (no movement by any UAV) and clear stuck targets
        if self.last_positions == self.positions:
            self.stall_count += 1
            if self.stall_count >= 3:
                self.targets = [None] * self.n_agents
                self.paths = [[] for _ in range(self.n_agents)]
        else:
            self.stall_count = 0
        self.last_positions = list(self.positions)

        # Recompute targets if reached or invalid
        for i, pos in enumerate(self.positions):
            if self.targets[i] is not None and self.targets[i] == pos:
                self.targets[i] = None
                self.paths[i] = []
            if self.targets[i] is not None and not self.map.has_node(self.targets[i]):
                self.targets[i] = None
                self.paths[i] = []

        # Assign new targets where needed
        self._assign_targets(phase)

        # Plan next hops along shortest known paths
        actions: List[int] = []
        planned_next: Dict[int, int] = {}  # node_id -> agent_id that wants to move there
        for i, pos in enumerate(self.positions):
            target = self.targets[i]
            if target is None:
                actions.append(pos)  # wait
                continue

            if not self.paths[i] or self.paths[i][0] != pos:
                self.paths[i] = self.map.shortest_path(pos, target)

            if len(self.paths[i]) >= 2:
                nxt = self.paths[i][1]
            else:
                nxt = pos

            # Collision: another UAV already plans to end on nxt
            if nxt in planned_next:
                nxt = pos  # wait one tick
            elif nxt != pos:
                # Edge-swap check: other UAV moving opposite direction
                other_i = planned_next.get(pos)
                if other_i is not None:
                    other_pos = self.positions[other_i]
                    if other_pos == nxt:
                        nxt = pos  # would swap edges, wait instead

            planned_next[nxt] = i
            actions.append(nxt)

        return actions

    def _assign_targets(self, phase: str) -> None:
        """Assign one target per UAV without a current target."""
        open_slots = [i for i, t in enumerate(self.targets) if t is None]
        if not open_slots:
            return

        if phase == "explore":
            candidates = self._explore_candidates()
        else:
            candidates = self._surveil_candidates()

        if not candidates:
            return

        # Greedy assignment: for each open slot, pick the cheapest candidate
        # that hasn't been claimed yet. Recompute costs each iteration because
        # claiming a target changes the pool.
        claimed: Set[int] = set()
        for i in open_slots:
            pos = self.positions[i]
            best: Optional[Tuple[int, float]] = None
            for cand in candidates:
                if cand in claimed or cand == pos:
                    continue
                path = self.map.shortest_path(pos, cand)
                if not path:
                    continue
                cost = self.map.path_cost(path)
                if best is None or cost < best[1]:
                    best = (cand, cost)
            if best is not None:
                self.targets[i] = best[0]
                self.paths[i] = self.map.shortest_path(pos, best[0])
                claimed.add(best[0])

    def _explore_candidates(self) -> List[int]:
        """Return high-value exploration targets (unvisited known frontier nodes)."""
        known = set(self.map.graph.nodes())
        if not known:
            return []

        # Priority 1: unvisited known nodes that are likely frontier (leaf-ish).
        unvisited = known - self.map.visited
        if unvisited:
            # Prefer nodes with low known degree (leads to new areas) and far
            # from visited set (spreads agents out).
            scored = []
            for node in unvisited:
                degree = self.map.graph.degree(node)
                dist_to_visited = self._min_distance_to_set(node, self.map.visited)
                # Score: prefer leaves and nodes away from visited area.
                score = -degree * 10 + dist_to_visited
                scored.append((score, node))
            scored.sort(reverse=True)
            return [n for _, n in scored[:50]]

        # Fallback: if everything known is visited, pick visited nodes with
        # highest distance to visited neighbors to push observation frontier.
        scored = []
        for node in known:
            dist_to_visited = self._min_distance_to_set(node, self.map.visited - {node})
            scored.append((dist_to_visited, node))
        scored.sort(reverse=True)
        return [n for _, n in scored[:30]]

    def _surveil_candidates(self) -> List[int]:
        """Return nodes that still need re-observation during surveillance."""
        known = set(self.map.graph.nodes())
        need = known - self.surveil_seen
        if not need:
            return []
        # Prefer nodes farthest from already surveilled nodes to maximize spread
        scored = []
        for node in need:
            dist = self._min_distance_to_set(node, self.surveil_seen)
            scored.append((dist, node))
        scored.sort(reverse=True)
        return [n for _, n in scored[:50]]

    def _min_distance_to_set(self, node: int, target_set: Set[int]) -> float:
        if node in target_set or not target_set:
            return 0.0
        min_dist = float("inf")
        pos = self.map.positions.get(node)
        for t in target_set:
            t_pos = self.map.positions.get(t)
            if pos and t_pos:
                d = math.dist(pos, t_pos)
            else:
                d = 0.0
            if d < min_dist:
                min_dist = d
        return min_dist if min_dist != float("inf") else 0.0
