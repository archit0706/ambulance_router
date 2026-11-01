import time
import heapq
from collections import deque
from dataclasses import dataclass
from cost_model import min_edge_cost, min_edge_length
from heuristics import make_heuristic

@dataclass
class SearchResult:
    path: list
    cost: float
    distance_m: float
    nodes_explored: int
    runtime: float
    peak_frontier: int

def build_path(parent, start, goal):
    path = []
    curr = goal
    while curr is not None:
        path.append(curr)
        if curr == start:
            break
        curr = parent.get(curr)
    path.reverse()
    if not path or path[0] != start:
        return []
    return path

def score_path(G, path):
    if len(path) < 2:
        return 0.0, 0.0
    total_cost = 0.0
    total_dist = 0.0
    for i in range(len(path) - 1):
        u, v = path[i], path[i + 1]
        total_cost += min_edge_cost(G, u, v)
        total_dist += min_edge_length(G, u, v)
    return total_cost, total_dist

def bfs(G, start, goal):
    t0 = time.perf_counter()
    if start == goal:
        return SearchResult([start], 0.0, 0.0, 1, time.perf_counter() - t0, 1)

    q = deque([start])
    visited = {start}
    parent = {start: None}
    explored = 0
    peak = 1

    while q:
        if len(q) > peak:
            peak = len(q)
        u = q.popleft()
        explored += 1

        if u == goal:
            path = build_path(parent, start, goal)
            cost, dist = score_path(G, path)
            return SearchResult(path, cost, dist, explored, time.perf_counter() - t0, peak)

        for v in G.neighbors(u):
            if v not in visited:
                visited.add(v)
                parent[v] = u
                q.append(v)

    return SearchResult([], float("inf"), float("inf"), explored, time.perf_counter() - t0, peak)

def dfs(G, start, goal):
    t0 = time.perf_counter()
    if start == goal:
        return SearchResult([start], 0.0, 0.0, 1, time.perf_counter() - t0, 1)

    stack = [start]
    visited = set()
    parent = {start: None}
    explored = 0
    peak = 1

    while stack:
        if len(stack) > peak:
            peak = len(stack)
        u = stack.pop()
        if u in visited:
            continue
        visited.add(u)
        explored += 1

        if u == goal:
            path = build_path(parent, start, goal)
            cost, dist = score_path(G, path)
            return SearchResult(path, cost, dist, explored, time.perf_counter() - t0, peak)

        for v in G.neighbors(u):
            if v not in visited:
                parent[v] = u
                stack.append(v)

    return SearchResult([], float("inf"), float("inf"), explored, time.perf_counter() - t0, peak)

def dijkstra(G, start, goal):
    t0 = time.perf_counter()
    if start == goal:
        return SearchResult([start], 0.0, 0.0, 1, time.perf_counter() - t0, 1)

    pq = [(0.0, start)]
    g_score = {start: 0.0}
    parent = {start: None}
    closed = set()
    explored = 0
    peak = 1

    while pq:
        if len(pq) > peak:
            peak = len(pq)
        cost_u, u = heapq.heappop(pq)
        if u in closed:
            continue
        closed.add(u)
        explored += 1

        if u == goal:
            path = build_path(parent, start, goal)
            _, dist = score_path(G, path)
            return SearchResult(path, cost_u, dist, explored, time.perf_counter() - t0, peak)

        for v in G.neighbors(u):
            if v in closed:
                continue
            w = min_edge_cost(G, u, v)
            new_cost = cost_u + w
            if new_cost < g_score.get(v, float("inf")):
                g_score[v] = new_cost
                parent[v] = u
                heapq.heappush(pq, (new_cost, v))

    return SearchResult([], float("inf"), float("inf"), explored, time.perf_counter() - t0, peak)

def astar(G, start, goal, h_func=None):
    t0 = time.perf_counter()
    if start == goal:
        return SearchResult([start], 0.0, 0.0, 1, time.perf_counter() - t0, 1)

    if h_func is None:
        h_func = make_heuristic(G)

    pq = [(h_func(start, goal), 0.0, start)]
    g_score = {start: 0.0}
    parent = {start: None}
    closed = set()
    explored = 0
    peak = 1

    while pq:
        if len(pq) > peak:
            peak = len(pq)
        f_u, cost_u, u = heapq.heappop(pq)
        if u in closed:
            continue
        closed.add(u)
        explored += 1

        if u == goal:
            path = build_path(parent, start, goal)
            _, dist = score_path(G, path)
            return SearchResult(path, cost_u, dist, explored, time.perf_counter() - t0, peak)

        for v in G.neighbors(u):
            if v in closed:
                continue
            w = min_edge_cost(G, u, v)
            new_cost = cost_u + w
            if new_cost < g_score.get(v, float("inf")):
                g_score[v] = new_cost
                parent[v] = u
                f_v = new_cost + h_func(v, goal)
                heapq.heappush(pq, (f_v, new_cost, v))

    return SearchResult([], float("inf"), float("inf"), explored, time.perf_counter() - t0, peak)