BASE_TRAFFIC_MULTIPLIER = 1.8

ZONE_EXTRA = {
    "normal": 0.0,
    "main_road": 0.4,
    "kutchery_chowk": 0.5,
    "albert_ekka": 0.4,
    "lalpur": 0.4,
    "ratu_road": 0.3,
}

SIGNAL_PENALTY_SEC = 20.0
RESIDENTIAL_PENALTY_SEC = 5.0
AMBULANCE_SPEED_FACTOR = 1.2
MAIN_ROADS = {"trunk", "trunk_link", "primary", "primary_link", "secondary", "secondary_link"}

def get_hw_type(data):
    hw = data.get("highway", "residential")
    if isinstance(hw, list):
        return str(hw[0])
    if isinstance(hw, str) and hw.startswith("["):
        return hw.strip("[]'\" ").split(",")[0].strip("'\" ")
    return str(hw)

def edge_cost(data):
    length_m = float(data.get("length", 1.0))
    spd_kph = float(data.get("speed_kph", 40.0))
    hw = get_hw_type(data)

    if hw in MAIN_ROADS:
        spd_kph *= AMBULANCE_SPEED_FACTOR

    spd_mps = spd_kph / 3.6
    base_time = length_m / spd_mps

    zone = str(data.get("zone", "normal"))
    mult = BASE_TRAFFIC_MULTIPLIER + ZONE_EXTRA.get(zone, 0.0)

    sig_pen = SIGNAL_PENALTY_SEC if str(data.get("signal_at_v", "0")) == "1" else 0.0
    road_pen = RESIDENTIAL_PENALTY_SEC if hw in {"residential", "living_street", "unclassified"} else 0.0

    return (base_time * mult) + sig_pen + road_pen

def min_edge_cost(G, u, v):
    edges = G[u][v]
    return min(edge_cost(d) for d in edges.values())

def min_edge_length(G, u, v):
    edges = G[u][v]
    return min(float(d.get("length", 1.0)) for d in edges.values())