import os
import random
import osmnx as ox
import networkx as nx
import pandas as pd

GRAPH_PATH = os.path.join("data", "ranchi.graphml")
HOSPITALS_PATH = os.path.join("data", "hospitals.csv")
MAX_SPEED_KPH = 80.0

RANCHI_CENTER = (23.3600, 85.3250)
RANCHI_RADIUS_M = 8000

ZONES = {
    "main_road": (23.350, 23.372, 85.320, 85.330),
    "kutchery_chowk": (23.372, 23.382, 85.322, 85.332),
    "albert_ekka": (23.365, 23.372, 85.324, 85.332),
    "lalpur": (23.368, 23.380, 85.335, 85.348),
    "ratu_road": (23.375, 23.390, 85.295, 85.322),
}

def get_zone(lat, lon):
    for name, (lat_min, lat_max, lon_min, lon_max) in ZONES.items():
        if lat_min <= lat <= lat_max and lon_min <= lon <= lon_max:
            return name
    return "normal"

def annotate_graph(G):
    for u, v, k, data in G.edges(keys=True, data=True):
        if "speed_kph" in data:
            spd = float(data["speed_kph"])
        else:
            spd = 40.0
        spd = min(spd, MAX_SPEED_KPH)
        data["speed_kph"] = spd

        length_m = float(data.get("length", 1.0))
        data["length"] = length_m
        data["base_time"] = length_m / (spd / 3.6)

        lat_u, lon_u = float(G.nodes[u]["y"]), float(G.nodes[u]["x"])
        lat_v, lon_v = float(G.nodes[v]["y"]), float(G.nodes[v]["x"])
        lat_mid = (lat_u + lat_v) / 2.0
        lon_mid = (lon_u + lon_v) / 2.0

        data["lat_mid"] = lat_mid
        data["lon_mid"] = lon_mid
        data["zone"] = get_zone(lat_mid, lon_mid)

        v_hw = G.nodes[v].get("highway", "")
        data["signal_at_v"] = "1" if v_hw == "traffic_signals" else "0"

    return G

def load_or_build_graph():
    if os.path.exists(GRAPH_PATH):
        G = ox.load_graphml(GRAPH_PATH)
        for u, v, k, data in G.edges(keys=True, data=True):
            data["length"] = float(data["length"])
            data["speed_kph"] = float(data["speed_kph"])
            data["base_time"] = float(data["base_time"])
            data["lat_mid"] = float(data["lat_mid"])
            data["lon_mid"] = float(data["lon_mid"])
            data["signal_at_v"] = str(data.get("signal_at_v", "0"))
            data["zone"] = str(data.get("zone", "normal"))
        return G

    os.makedirs("data", exist_ok=True)
    ox.settings.requests_timeout = 300
    ox.settings.use_cache = True

    try:
        G = ox.graph_from_point(RANCHI_CENTER, dist=RANCHI_RADIUS_M, network_type="drive")
    except Exception:
        ox.settings.overpass_url = "https://overpass.kumi.systems/api/interpreter"
        G = ox.graph_from_point(RANCHI_CENTER, dist=RANCHI_RADIUS_M, network_type="drive")

    G = ox.routing.add_edge_speeds(G)
    G = ox.routing.add_edge_travel_times(G)

    scc = max(nx.strongly_connected_components(G), key=len)
    G = G.subgraph(scc).copy()

    G = annotate_graph(G)
    ox.save_graphml(G, GRAPH_PATH)
    return G

def load_hospitals(G):
    df = pd.read_csv(HOSPITALS_PATH)
    nodes = ox.distance.nearest_nodes(G, df["lon"].tolist(), df["lat"].tolist())
    df["node"] = nodes
    return df.to_dict(orient="records")

def get_ambulances(G, x=8, seed=42):
    rng = random.Random(seed)
    nodes = sorted(list(G.nodes()))
    return rng.sample(nodes, min(x, len(nodes)))

if __name__ == "__main__":
    print("Building or loading Ranchi graph...")
    G = load_or_build_graph()
    hospitals = load_hospitals(G)
    ambulances = get_ambulances(G, x=8)
    print(f"Nodes: {len(G.nodes)}, Edges: {len(G.edges)}")
    print(f"Loaded {len(hospitals)} hospitals and placed {len(ambulances)} ambulances.")