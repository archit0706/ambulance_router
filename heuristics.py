import math
from cost_model import BASE_TRAFFIC_MULTIPLIER, AMBULANCE_SPEED_FACTOR, MAIN_ROADS, get_hw_type

def haversine_m(lat1, lon1, lat2, lon2):
    r = 6371000.0
    p1 = math.radians(lat1)
    p2 = math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2.0) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2.0) ** 2
    return 2.0 * r * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))

def compute_v_eff_mps(G):
    v_max_kph = 0.0
    for _, _, data in G.edges(data=True):
        spd = float(data.get("speed_kph", 40.0))
        hw = get_hw_type(data)
        if hw in MAIN_ROADS:
            spd *= AMBULANCE_SPEED_FACTOR
        if spd > v_max_kph:
            v_max_kph = spd
    if v_max_kph <= 0.0:
        v_max_kph = 80.0 * AMBULANCE_SPEED_FACTOR
    v_eff_kph = v_max_kph / BASE_TRAFFIC_MULTIPLIER
    return v_eff_kph / 3.6

def make_heuristic(G):
    v_eff_mps = compute_v_eff_mps(G)
    coords = {n: (float(d["y"]), float(d["x"])) for n, d in G.nodes(data=True)}

    def h(u, goal):
        lat1, lon1 = coords[u]
        lat2, lon2 = coords[goal]
        dist_m = haversine_m(lat1, lon1, lat2, lon2)
        return dist_m / v_eff_mps

    return h