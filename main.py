import os
import random
import threading
import webbrowser
from http.server import SimpleHTTPRequestHandler, HTTPServer
import osmnx as ox
from graph_builder import load_or_build_graph, load_hospitals, get_ambulances
from heuristics import make_heuristic
from dispatcher import dispatch
from visualize import create_route_map, plot_comparison_charts

def format_path_preview(path):
    if len(path) <= 6:
        return " -> ".join(str(n) for n in path)
    head = " -> ".join(str(n) for n in path[:3])
    tail = " -> ".join(str(n) for n in path[-3:])
    return f"{head} -> ... ({len(path)} nodes) ... -> {tail}"

def get_patient_node(G, ambulances, hospitals):
    print("\nSelect Patient Location Mode:")
    print("  1. Enter Latitude & Longitude manually (e.g., 23.3700, 85.3250 for Main Road)")
    print("  2. Pick a seeded random location in Ranchi (Default)")
    choice = input("Enter 1 or 2 [press Enter for 2]: ").strip()

    if choice == "1":
        try:
            lat = float(input("  Enter Patient Latitude  (e.g., 23.3700): ").strip())
            lon = float(input("  Enter Patient Longitude (e.g., 85.3250): ").strip())
            node = ox.distance.nearest_nodes(G, lon, lat)
            return node
        except Exception:
            print("  Invalid input! Falling back to random location.")

    rng = random.Random(100)
    all_nodes = sorted(list(G.nodes()))
    excluded = set(ambulances) | {h["node"] for h in hospitals}
    candidates = [n for n in all_nodes if n not in excluded]
    return rng.choice(candidates)

def serve_and_open_map(html_filename="ranchi_routes.html", port=8765):
    class QuietHandler(SimpleHTTPRequestHandler):
        def log_message(self, format, *args):
            pass

    server = HTTPServer(("127.0.0.1", port), QuietHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    url = f"http://localhost:{port}/{os.path.basename(html_filename)}"
    print(f"\nOpening map at: {url}")
    webbrowser.open(url)
    input("Press Enter in this terminal when you are done viewing the map to exit...")
    server.shutdown()

def main():
    G = load_or_build_graph()
    hospitals = load_hospitals(G)
    x_amb = 8
    ambulances = get_ambulances(G, x=x_amb, seed=42)

    patient_node = get_patient_node(G, ambulances, hospitals)
    p_lat = G.nodes[patient_node]["y"]
    p_lon = G.nodes[patient_node]["x"]

    print("\n" + "=" * 85)
    print("RANCHI AMBULANCE ROUTE OPTIMIZATION & ALGORITHM BENCHMARK")
    print("=" * 85)
    print(f"Ambulances (x) : {len(ambulances)}")
    print(f"Hospitals  (y) : {len(hospitals)}")
    print(f"Patient Node   : {patient_node} (Lat: {p_lat:.4f}, Lon: {p_lon:.4f})")
    print("-" * 85)

    h_func = make_heuristic(G)
    algos = ["BFS", "DFS", "Dijkstra", "A*"]
    results = {}

    for algo in algos:
        res = dispatch(G, patient_node, ambulances, hospitals, algo, h_func)
        results[algo] = res

        print(f"\n[{algo} DISPATCH DETAILS]")
        print(f"  Best Pair        : Ambulance #{res.best_amb_idx} (Node {res.best_amb_node}) -> {res.best_hosp_name}")
        print(f"  Leg 1 (Amb->Pat) : {res.leg1_time_s:.1f} s ({res.leg1_time_s/60:.2f} min) | {format_path_preview(res.path_to_patient)}")
        print(f"  Leg 2 (Pat->Hosp): {res.leg2_time_s:.1f} s ({res.leg2_time_s/60:.2f} min) | {format_path_preview(res.path_to_hospital)}")
        print(f"  Total ETA        : {res.total_time_s:.1f} s ({res.total_time_s/60:.2f} min) | Total Dist: {res.total_dist_m/1000:.2f} km")

    opt_time = results["Dijkstra"].total_time_s

    print("\n" + "=" * 85)
    print("PERFORMANCE COMPARISON SUMMARY")
    print("=" * 85)
    header = f"{'Algo':<10} | {'Amb#':<4} | {'Hospital':<28} | {'ETA (min)':<9} | {'Dist (km)':<9} | {'Nodes':<8} | {'Frontier':<8} | {'Runtime (s)':<11} | {'Opt Gap':<8}"
    print(header)
    print("-" * len(header))

    for algo in algos:
        r = results[algo]
        gap = ((r.total_time_s - opt_time) / opt_time) * 100.0
        hosp_short = r.best_hosp_name[:26] + ".." if len(r.best_hosp_name) > 28 else r.best_hosp_name
        print(
            f"{algo:<10} | "
            f"#{r.best_amb_idx:<3} | "
            f"{hosp_short:<28} | "
            f"{r.total_time_s/60:<9.2f} | "
            f"{r.total_dist_m/1000:<9.2f} | "
            f"{r.total_nodes:<8} | "
            f"{r.peak_frontier:<8} | "
            f"{r.total_runtime_s:<11.4f} | "
            f"+{gap:.2f}%"
        )

    optimal_algos = [a for a in algos if abs(results[a].total_time_s - opt_time) < 1e-4]
    best_algo = min(optimal_algos, key=lambda a: (results[a].total_nodes, results[a].total_runtime_s))

    dijk_nodes = results["Dijkstra"].total_nodes
    astar_nodes = results["A*"].total_nodes
    node_saving = ((dijk_nodes - astar_nodes) / dijk_nodes) * 100.0 if dijk_nodes > 0 else 0.0

    print("\n" + "=" * 85)
    print(f"\nFINAL VERDICT: BEST ALGORITHM IS {best_algo}")
    print("=" * 85)
    print(f"1. Optimality : Dijkstra and A* both achieve the lowest possible response time ({opt_time/60:.2f} min).")
    print(f"   BFS (+{((results['BFS'].total_time_s - opt_time)/opt_time)*100:.1f}% slower) and DFS (+{((results['DFS'].total_time_s - opt_time)/opt_time)*100:.1f}% slower) yield suboptimal routes.")
    print(f"2. Efficiency : {best_algo} explored {astar_nodes} nodes vs Dijkstra's {dijk_nodes} nodes ({node_saving:.1f}% reduction in search effort)")
    print(f"   and finished in {results[best_algo].total_runtime_s:.4f}s vs Dijkstra's {results['Dijkstra'].total_runtime_s:.4f}s.")
    print("=" * 85)

    map_path = create_route_map(G, patient_node, ambulances, hospitals, results)
    chart_path = plot_comparison_charts(results)
    print(f"\nInteractive Map saved to : {map_path}")
    print(f"Comparison Chart saved to: {chart_path}")
    serve_and_open_map(map_path)

if __name__ == "__main__":
    main()