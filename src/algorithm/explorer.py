"""SCOUT submission for EDTH 01-ats: 3D Graph Exploration & Surveillance.

Frontier-based exploration with greedy multi-agent coordination and a
pre-planned surveillance routing phase. Uses Euclidean distance for frontier
selection (fast) and Dijkstra only for the chosen target.

Usage:
    cd challenge/graph_explo
    uv run run_eval.py --submission ../../src/algorithm/explorer.py \
        --graphs graphs/train --quiet

Only stdlib + networkx are used.
"""

from __future__ import annotations

import math
import random
from typing import Dict, List, Optional, Set, Tuple

import networkx as nx

try:
    from exploration_challenge.observation import Observation
except ImportError:  # pragma: no cover
    Observation = object  # type: ignore


class _Map:
    """Persistent map built from merging UAV observations."""

    def __init__(self) -> None:
        self.graph = nx.Graph()
        self.visited: Set[int] = set()
        self.positions: Dict[int, Tuple[float, float, float]] = {}

    def merge(self, observations: List[Observation]) -> None:
        for obs in observations:
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

    def shortest_path(self, source: int, target: int) -> List[int]:
        if source == target:
            return [source]
        try:
            return nx.shortest_path(self.graph, source, target, weight="weight")
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            return []


class Explorer:
    """Centralized policy for 1-3 UAVs."""

    def __init__(self, sensor_k: int = 4) -> None:
        self.map = _Map()
        self.rng = random.Random(0)
        self.sensor_k = sensor_k
        self.n_agents = 3
        self.positions: List[int] = []
        self.targets: List[Optional[int]] = [None] * self.n_agents
        self.paths: List[List[int]] = [[] for _ in range(self.n_agents)]
        self.explore_seen: Set[int] = set()
        self.surveil_seen: Set[int] = set()
        self.last_positions: Optional[List[int]] = None
        self.stall_count = 0
        self._path_cache: Dict[Tuple[int, int], List[int]] = {}
        self._surveil_routes: Optional[List[List[int]]] = None
        self._route_idx: List[int] = [0, 0, 0]

    def reset(
        self,
        starts: List[int],
        observations: List[Observation],
        seed: Optional[int] = None,
    ) -> None:
        self.rng = random.Random(seed)
        self.n_agents = len(starts)
        self.map = _Map()
        self.map.merge(observations)
        self.positions = list(starts)
        self.targets = [None] * self.n_agents
        self.paths = [[] for _ in range(self.n_agents)]
        self.explore_seen = set()
        self.surveil_seen = set()
        self.last_positions = None
        self.stall_count = 0
        self._path_cache = {}
        self._surveil_routes = None
        self._route_idx = [0] * self.n_agents
        self._explore_stagnation = 0
        self._last_explored_count = -1
        for obs in observations:
            self.explore_seen.update(n.id for n in obs.nodes)

    def step(self, observations: List[Observation], phase: str) -> List[int]:
        self.map.merge(observations)
        self.positions = [obs.position for obs in observations]

        for obs in observations:
            if phase == "explore":
                self.explore_seen.update(n.id for n in obs.nodes)
            else:
                self.surveil_seen.update(n.id for n in obs.nodes)

        # Stall recovery.
        if self.last_positions == self.positions:
            self.stall_count += 1
            if self.stall_count >= 3:
                self.targets = [None] * self.n_agents
                self.paths = [[] for _ in range(self.n_agents)]
                self._path_cache = {}
                self._surveil_routes = None
        else:
            self.stall_count = 0
        self.last_positions = list(self.positions)

        # Clear reached/invalid targets.
        for i, pos in enumerate(self.positions):
            if self.targets[i] == pos:
                self.targets[i] = None
                self.paths[i] = []
            if self.targets[i] is not None and not self.map.graph.has_node(self.targets[i]):
                self.targets[i] = None
                self.paths[i] = []

        if phase == "explore":
            self._assign_explore_targets()
        else:
            self._assign_surveil_targets()

        actions: List[int] = []
        planned_next: Dict[int, int] = {}
        for i, pos in enumerate(self.positions):
            target = self.targets[i]
            if target is None:
                actions.append(pos)
                continue

            if not self.paths[i] or self.paths[i][0] != pos:
                self.paths[i] = self._cached_path(pos, target)

            nxt = self.paths[i][1] if len(self.paths[i]) >= 2 else pos

            # Collision avoidance.
            if nxt in planned_next:
                nxt = pos
            elif nxt != pos:
                other_i = planned_next.get(pos)
                if other_i is not None and self.positions[other_i] == nxt:
                    nxt = pos

            planned_next[nxt] = i
            actions.append(nxt)

        return actions

    def _cached_path(self, source: int, target: int) -> List[int]:
        key = (source, target)
        if key not in self._path_cache:
            self._path_cache[key] = self.map.shortest_path(source, target)
        return self._path_cache[key]

    def _euclidean(self, a: int, b: int) -> float:
        pa = self.map.positions.get(a)
        pb = self.map.positions.get(b)
        if pa is None or pb is None:
            return float("inf")
        return math.dist(pa, pb)

    def _assign_explore_targets(self) -> None:
        """Assign nearest unvisited known node to each UAV.

        If exploration progress stalls (observed fraction stops growing), switch
        to classic frontier mode (unvisited nodes adjacent to visited nodes) to
        push the visibility boundary outward.
        """
        open_slots = [i for i, t in enumerate(self.targets) if t is None]
        if not open_slots:
            return

        known = set(self.map.graph.nodes())
        if not known:
            return

        current_observed = len(self.explore_seen)
        if getattr(self, "_last_explored_count", None) == current_observed:
            self._explore_stagnation = getattr(self, "_explore_stagnation", 0) + 1
        else:
            self._explore_stagnation = 0
        self._last_explored_count = current_observed

        unvisited = known - self.map.visited
        if not unvisited:
            unvisited = known
        if not unvisited:
            return

        # If stagnating, prefer classic frontier nodes (unvisited neighbors of visited).
        if self._explore_stagnation >= 20:
            frontier: Set[int] = set()
            for v in self.map.visited:
                frontier.update(n for n in self.map.graph.neighbors(v) if n not in self.map.visited)
            if frontier:
                candidates = sorted(frontier, key=lambda n: self.map.graph.degree(n))[:300]
            else:
                candidates = sorted(unvisited, key=lambda n: self.map.graph.degree(n))[:300]
        else:
            candidates = sorted(unvisited, key=lambda n: self.map.graph.degree(n))[:300]

        # Partition candidates among agents by Euclidean proximity (Voronoi).
        assignment: Dict[int, List[int]] = {i: [] for i in open_slots}
        claimed: Set[int] = set(t for t in self.targets if t is not None)
        claimed.update(self.positions)

        for node in candidates:
            if node in claimed:
                continue
            best_i = min(open_slots, key=lambda i: self._euclidean(self.positions[i], node))
            assignment[best_i].append(node)

        for i in open_slots:
            pos = self.positions[i]
            cand = assignment[i]
            if not cand:
                continue
            target = min(cand, key=lambda n: self._euclidean(pos, n))
            self.targets[i] = target
            self.paths[i] = self._cached_path(pos, target)

    def _k_hop_ball(self, source: int) -> Set[int]:
        seen: Set[int] = {source}
        frontier: Set[int] = {source}
        for _ in range(self.sensor_k):
            nxt: Set[int] = set()
            for node in frontier:
                nxt.update(self.map.graph.neighbors(node))
            nxt -= seen
            seen.update(nxt)
            frontier = nxt
            if not frontier:
                break
        return seen

    def _assign_surveil_targets(self) -> None:
        """Adaptive surveillance: each UAV targets the nearest un-surveilled node
        in its Voronoi cell, recomputed every step."""
        open_slots = [i for i, t in enumerate(self.targets) if t is None]
        if not open_slots:
            return

        known = set(self.map.graph.nodes())
        need = known - self.surveil_seen
        if not need:
            return

        # Partition remaining need among agents by Euclidean proximity.
        assignment: Dict[int, List[int]] = {i: [] for i in open_slots}
        claimed: Set[int] = set(t for t in self.targets if t is not None)
        claimed.update(self.positions)

        for node in need:
            if node in claimed:
                continue
            best_i = min(open_slots, key=lambda i: self._euclidean(self.positions[i], node))
            assignment[best_i].append(node)

        for i in open_slots:
            pos = self.positions[i]
            candidates = assignment[i]
            if not candidates:
                # Fallback: nearest any need.
                candidates = [n for n in need if n != pos]
                if not candidates:
                    continue
            target = min(candidates, key=lambda n: self._euclidean(pos, n))
            self.targets[i] = target
            self.paths[i] = self._cached_path(pos, target)

    def _build_surveil_routes(self, known: Set[int]) -> List[List[int]]:
        """Partition a sampled set of nodes among agents and build TSP routes."""
        need = known - self.surveil_seen
        if not need:
            return [[] for _ in range(self.n_agents)]

        # Sample nodes to use as vantage points (all if small, otherwise sample).
        sample = list(need)
        if len(sample) > 300:
            self.rng.shuffle(sample)
            sample = sample[:300]

        # Partition sampled nodes among agents by start proximity (Voronoi).
        routes: List[List[int]] = [[] for _ in range(self.n_agents)]
        for node in sample:
            best_i = min(range(self.n_agents), key=lambda i: self._euclidean(self.positions[i], node))
            routes[best_i].append(node)

        # Build nearest-neighbor TSP routes for each agent.
        for i in range(self.n_agents):
            route = routes[i]
            if not route:
                continue
            ordered: List[int] = []
            current = self.positions[i]
            remaining = set(route)
            while remaining:
                nxt = min(remaining, key=lambda n: self._euclidean(current, n))
                ordered.append(nxt)
                remaining.remove(nxt)
                current = nxt
            routes[i] = ordered

        return routes
