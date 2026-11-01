import os
import folium
import matplotlib.pyplot as plt

ALGO_COLORS = {
    "BFS": ("#ff7f00", "#fdbf6f"),
    "DFS": ("#e31a1c", "#fb9a99"),
    "Dijkstra": ("#1f78b4", "#a6cee3"),
    "A*": ("#33a02c", "#b2df8a"),
}

def path_to_coords(G, path):
    return [(float(G.nodes[n]["y"]), float(G.nodes[n]["x"])) for n in path]

def create_route_map(G, patient_node, ambulances, hospitals, results, out_html="ranchi_routes.html"):
    p_lat = float(G.nodes[patient_node]["y"])
    p_lon = float(G.nodes[patient_node]["x"])

    m = folium.Map(
        location=[p_lat, p_lon],
        zoom_start=13,
        tiles=None,
    )

    folium.TileLayer(
        tiles="https://mt1.google.com/vt/lyrs=m&x={x}&y={y}&z={z}",
        attr="Map data © Google | Route Graph © OpenStreetMap contributors",
        name="Google Streets (Recommended)",
        control=True,
    ).add_to(m)

    folium.TileLayer(
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{z}/{y}/{x}",
        attr="Tiles © Esri | Data © OpenStreetMap contributors",
        name="Esri World Street Map",
        control=True,
    ).add_to(m)

    markers_fg = folium.FeatureGroup(name="Ambulances, Hospitals & Patient", show=True)

    for i, a_node in enumerate(ambulances):
        lat = float(G.nodes[a_node]["y"])
        lon = float(G.nodes[a_node]["x"])
        folium.Marker(
            location=[lat, lon],
            popup=f"Ambulance #{i} (Node {a_node})",
            tooltip=f"Ambulance #{i}",
            icon=folium.Icon(color="blue", icon="ambulance", prefix="fa"),
        ).add_to(markers_fg)

    for h in hospitals:
        h_node = h["node"]
        lat = float(G.nodes[h_node]["y"])
        lon = float(G.nodes[h_node]["x"])
        folium.Marker(
            location=[lat, lon],
            popup=f"Hospital: {h['name']}",
            tooltip=h["name"],
            icon=folium.Icon(color="red", icon="plus-sign"),
        ).add_to(markers_fg)

    folium.Marker(
        location=[p_lat, p_lon],
        popup=f"Patient Location (Node {patient_node})",
        tooltip="PATIENT EMERGENCY",
        icon=folium.Icon(color="green", icon="user"),
    ).add_to(markers_fg)

    markers_fg.add_to(m)

    for algo, res in results.items():
        show_default = algo in {"A*", "BFS"}
        fg = folium.FeatureGroup(
            name=f"{algo} Route (ETA: {res.total_time_s/60:.1f} min, Dist: {res.total_dist_m/1000:.2f} km)",
            show=show_default,
        )
        c1, c2 = ALGO_COLORS.get(algo, ("#000000", "#555555"))

        if len(res.path_to_patient) >= 2:
            coords1 = path_to_coords(G, res.path_to_patient)
            folium.PolyLine(
                coords1,
                color=c1,
                weight=5,
                opacity=0.85,
                tooltip=f"{algo} Leg 1: Amb #{res.best_amb_idx} -> Patient ({res.leg1_time_s/60:.1f} min)",
            ).add_to(fg)

        if len(res.path_to_hospital) >= 2:
            coords2 = path_to_coords(G, res.path_to_hospital)
            folium.PolyLine(
                coords2,
                color=c1,
                weight=5,
                opacity=0.85,
                dash_array="8, 6",
                tooltip=f"{algo} Leg 2: Patient -> {res.best_hosp_name} ({res.leg2_time_s/60:.1f} min)",
            ).add_to(fg)

        fg.add_to(m)

    folium.LayerControl(collapsed=False).add_to(m)
    m.save(out_html)
    return os.path.abspath(out_html)

def plot_comparison_charts(results, out_png="algorithm_comparison.png"):
    algos = list(results.keys())
    etas = [results[a].total_time_s / 60.0 for a in algos]
    nodes = [results[a].total_nodes for a in algos]
    runtimes = [results[a].total_runtime_s * 1000.0 for a in algos]
    frontiers = [results[a].peak_frontier for a in algos]

    colors = ["#ff7f00", "#e31a1c", "#1f78b4", "#33a02c"]

    fig, axes = plt.subplots(2, 2, figsize=(12, 8))
    fig.suptitle("Ranchi Ambulance Routing: Algorithm Comparison", fontsize=14, fontweight="bold")

    ax1 = axes[0, 0]
    ax1.bar(algos, etas, color=colors)
    ax1.set_title("Total Response ETA (minutes - Lower is Better)")
    ax1.set_ylabel("Minutes (Log Scale)")
    ax1.set_yscale("log")
    for i, v in enumerate(etas):
        ax1.text(i, v, f"{v:.1f}m", ha="center", va="bottom", fontsize=9)

    ax2 = axes[0, 1]
    ax2.bar(algos, nodes, color=colors)
    ax2.set_title("Total Nodes Explored (Search Effort - Lower is Better)")
    ax2.set_ylabel("Nodes Expanded")
    for i, v in enumerate(nodes):
        ax2.text(i, v, f"{v}", ha="center", va="bottom", fontsize=9)

    ax3 = axes[1, 0]
    ax3.bar(algos, runtimes, color=colors)
    ax3.set_title("Total Dispatch Runtime (ms - Lower is Better)")
    ax3.set_ylabel("Milliseconds")
    for i, v in enumerate(runtimes):
        ax3.text(i, v, f"{v:.1f}ms", ha="center", va="bottom", fontsize=9)

    ax4 = axes[1, 1]
    ax4.bar(algos, frontiers, color=colors)
    ax4.set_title("Peak Frontier Size (Memory Proxy - Lower is Better)")
    ax4.set_ylabel("Max Nodes in Memory")
    for i, v in enumerate(frontiers):
        ax4.text(i, v, f"{v}", ha="center", va="bottom", fontsize=9)

    plt.tight_layout()
    plt.savefig(out_png, dpi=150)
    plt.close(fig)
    return os.path.abspath(out_png)