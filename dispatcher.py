from dataclasses import dataclass
from algorithms import bfs, dfs, dijkstra, astar
from heuristics import make_heuristic

@dataclass
class DispatchResult:
    algo_name: str
    best_amb_idx: int
    best_amb_node: int
    best_hosp_name: str
    best_hosp_node: int
    leg1_time_s: float
    leg2_time_s: float
    total_time_s: float
    total_dist_m: float
    path_to_patient: list
    path_to_hospital: list
    total_nodes: int
    total_runtime_s: float
    peak_frontier: int

def run_algo(G, u, v, algo_name, h_func=None):
    if algo_name == "BFS":
        return bfs(G, u, v)
    if algo_name == "DFS":
        return dfs(G, u, v)
    if algo_name == "Dijkstra":
        return dijkstra(G, u, v)
    if algo_name == "A*":
        return astar(G, u, v, h_func)
    raise ValueError(f"Unknown algorithm: {algo_name}")

def dispatch(G, patient_node, ambulances, hospitals, algo_name, h_func=None):
    if algo_name == "A*" and h_func is None:
        h_func = make_heuristic(G)

    best_amb_idx = -1
    best_amb_node = -1
    best_leg1 = None

    total_nodes = 0
    total_runtime = 0.0
    max_frontier = 0

    for i, a_node in enumerate(ambulances):
        res = run_algo(G, a_node, patient_node, algo_name, h_func)
        total_nodes += res.nodes_explored
        total_runtime += res.runtime
        if res.peak_frontier > max_frontier:
            max_frontier = res.peak_frontier

        if best_leg1 is None or res.cost < best_leg1.cost:
            best_leg1 = res
            best_amb_idx = i
            best_amb_node = a_node

    best_hosp_name = ""
    best_hosp_node = -1
    best_leg2 = None

    for h in hospitals:
        h_node = h["node"]
        res = run_algo(G, patient_node, h_node, algo_name, h_func)
        total_nodes += res.nodes_explored
        total_runtime += res.runtime
        if res.peak_frontier > max_frontier:
            max_frontier = res.peak_frontier

        if best_leg2 is None or res.cost < best_leg2.cost:
            best_leg2 = res
            best_hosp_name = h["name"]
            best_hosp_node = h_node

    total_time = best_leg1.cost + best_leg2.cost
    total_dist = best_leg1.distance_m + best_leg2.distance_m

    return DispatchResult(
        algo_name=algo_name,
        best_amb_idx=best_amb_idx,
        best_amb_node=best_amb_node,
        best_hosp_name=best_hosp_name,
        best_hosp_node=best_hosp_node,
        leg1_time_s=best_leg1.cost,
        leg2_time_s=best_leg2.cost,
        total_time_s=total_time,
        total_dist_m=total_dist,
        path_to_patient=best_leg1.path,
        path_to_hospital=best_leg2.path,
        total_nodes=total_nodes,
        total_runtime_s=total_runtime,
        peak_frontier=max_frontier,
    )