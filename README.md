# Ambulance Route Optimization System for Ranchi

A decision-support and pathfinding benchmark system designed for emergency medical dispatch in **Ranchi, Jharkhand, India**. Given $x$ available ambulances and $y$ curated hospitals across the city, the system selects the optimal `(Ambulance, Hospital)` pair and computes the fastest two-leg route (`Ambulance -> Patient -> Hospital`) while accounting for road speeds, peak-hour congestion zones, traffic signals, and road hierarchy.

It implements and benchmarks four classical graph search algorithms from scratch—**Breadth-First Search (BFS)**, **Depth-First Search (DFS)**, **Dijkstra's Algorithm**, and **A\* Search**—on the real OpenStreetMap drivable road network of Ranchi.

---

## Key Features

- **Real Ranchi Road Network (`OSMnx`):** Downloads and caches the directed drivable road graph of Ranchi (`data/ranchi.graphml`), preserving one-way constraints and extracting the largest strongly connected component (SCC) so every node is guaranteed to be reachable.
- **Multi-Factor Traffic Cost Model:** Evaluates edges using travel time rather than raw distance, incorporating:
  - Base travel time from road length and capped speed limits ($\le 80\text{ km/h}$).
  - Ambulance speed boost ($1.2\times$ normal speed on primary/trunk/secondary arteries).
  - Constant peak-hour traffic multiplier ($1.8\times$ base) plus hotspot congestion penalties ($+0.3$ to $+0.5$) across **Main Road, Kutchery Chowk, Albert Ekka Chowk, Lalpur, and Ratu Road**.
  - Traffic signal penalties ($+20\text{ s}$) and narrow residential road penalties ($+5\text{ s}$).
- **Four Search Algorithms Implemented from Scratch:**
  - `BFS` (Uninformed, queue-based, minimizes hop count).
  - `DFS` (Uninformed, iterative stack-based baseline).
  - `Dijkstra` (Uniform-cost min-heap search, optimal baseline).
  - `A*` (Informed min-heap search guided by an admissible scenario-aware Haversine effective-speed heuristic).
- **Two-Leg Optimal Dispatch Engine:** Evaluates all $x$ ambulances to the patient (Leg 1) and the patient to all $y$ hospitals (Leg 2) to minimize total time to treatment ($T = t_1 + t_2$).
- **Interactive Map & Performance Plots:** Exports a multi-layer `Folium` HTML map (`ranchi_routes.html`) with toggleable routes for each algorithm and a 4-panel `Matplotlib` comparison chart (`algorithm_comparison.png`).

---

## Project Structure

```text
ambulance_router/
├── data/
│   ├── hospitals.csv          # Curated Ranchi hospitals (name, lat, lon)
│   └── ranchi.graphml         # Cached OSMnx road network (auto-generated)
├── requirements.txt           # Python dependencies
├── graph_builder.py           # Downloads, annotates, and caches the Ranchi graph
├── cost_model.py              # Multi-factor edge cost function & traffic constants
├── heuristics.py              # Admissible Haversine effective-speed heuristic for A*
├── algorithms.py              # BFS, DFS, Dijkstra, and A* implementations
├── dispatcher.py              # Best (Ambulance, Hospital) pair selection logic
├── visualize.py               # Folium interactive map & Matplotlib bar charts
├── main.py                    # CLI entry point, benchmark runner & local map server
└── README.md                  # Project documentation
```

---

## Mathematical Formulation

### 1. Edge Cost Function
For every directed road segment $e = (u, v)$, the travel time cost in seconds is computed as:

$$\text{cost}(e) = \left( \frac{\text{length}(e)}{v_{\text{road}}(e)} \times M_{\text{traffic}}(e) \right) + P_{\text{signal}}(v) + P_{\text{road}}(e)$$

where:
- $v_{\text{road}}(e) = \text{speed}(e) \times 1.2$ on main roads (`trunk`, `primary`, `secondary`) and $\text{speed}(e)$ otherwise.
- $M_{\text{traffic}}(e) = 1.8 + Z_{\text{zone}}(e)$, where $Z_{\text{zone}}(e) \in [0.0, 0.5]$ depending on the Ranchi congestion zone.
- $P_{\text{signal}}(v) = 20\text{ s}$ if node $v$ has a traffic signal (`highway=traffic_signals`), else $0\text{ s}$.
- $P_{\text{road}}(e) = 5\text{ s}$ for residential/unclassified streets, else $0\text{ s}$.

### 2. Admissible A\* Heuristic
To guarantee optimality, the heuristic $h(n)$ must never overestimate the true remaining travel time to the goal:

$$h(n, \text{goal}) = \frac{d_{\text{haversine}}(n, \text{goal})}{v_{\text{eff}}}$$

where $d_{\text{haversine}}(n, \text{goal})$ is the great-circle straight-line distance in meters and $v_{\text{eff}} = \frac{v_{\max}}{M_{\min}}$ is the highest possible effective speed across the graph under the baseline traffic multiplier. Because straight-line distance is a lower bound on road distance and $v_{\text{eff}}$ is an upper bound on achievable speed, $h(n)$ is both **admissible** and **consistent**.

---

## Curated Ranchi Hospitals (`data/hospitals.csv`)

| Hospital Name | Latitude | Longitude |
| :--- | :---: | :---: |
| RIMS (Rajendra Institute of Medical Sciences) | `23.3911` | `85.3490` |
| Sadar Hospital | `23.3688` | `85.3255` |
| Medica Superspecialty Hospital | `23.3958` | `85.3578` |
| Orchid Medical Centre | `23.3752` | `85.3312` |
| HEC Hospital | `23.3105` | `85.2768` |
| Raj Hospital | `23.3562` | `85.3248` |
| Paras HEC Hospital | `23.3142` | `85.2815` |

---

## Installation & Setup

### Prerequisites
- Python `3.10+`
- Internet connection (required only on the first run to download the Ranchi map from OpenStreetMap)

### 1. Install Dependencies
Open a terminal inside the `ambulance_router/` folder and run:

```bash
pip install -r requirements.txt
```

### 2. Build & Cache the Ranchi Graph
Run `graph_builder.py` once to download the $8\text{ km}$ urban Ranchi road network, annotate congestion zones and traffic signals, and save `data/ranchi.graphml`:

```bash
python graph_builder.py
```
*(Subsequent runs load directly from `data/ranchi.graphml` in ~1–2 seconds.)*

### 3. Run the Dispatch Benchmark & Visualizer
```bash
python main.py
```
- Choose **Option 1** to enter custom patient coordinates inside Ranchi (Lat `23.28–23.44`, Lon `85.24–85.41`), or press **Enter (Option 2)** to use the seeded test scenario.
- The script prints the dispatch breakdown and benchmark table in the terminal, saves `algorithm_comparison.png`, and launches a local web server at `http://localhost:8765/ranchi_routes.html` to display the interactive route map.

---

## Sample Benchmark Results

For $x = 8$ ambulances, $y = 7$ hospitals ($15$ searches per algorithm), and Patient Node `5040905783` (`Lat: 23.3461, Lon: 85.3358`):

| Algorithm | Selected Pair | Total ETA (min) | Distance (km) | Nodes Explored | Peak Frontier | Runtime (s) | Optimality Gap |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **BFS** | Amb #1 $\rightarrow$ Raj Hospital | `24.92` | `6.46` | `154,737` | `450` | `0.1578` | `+35.21%` |
| **DFS** | Amb #2 $\rightarrow$ Raj Hospital | `1136.46` | `289.03` | `196,994` | `3,335` | `0.4538` | `+6066.78%` |
| **Dijkstra** | Amb #1 $\rightarrow$ Raj Hospital | **`18.43`** | **`6.31`** | `154,718` | `509` | `1.1203` | **`+0.00%`** |
| **A\*** | Amb #1 $\rightarrow$ Raj Hospital | **`18.43`** | **`6.31`** | **`62,301`** | **`426`** | **`0.5793`** | **`+0.00%`** |

### Key Takeaways
1. **Why BFS & DFS Fail Emergency Dispatch:** `BFS` minimizes intersection count (hops) rather than travel time, cutting through slow, congested inner streets and arriving **35.2% slower** (`24.92 min` vs `18.43 min`). `DFS` explores blindly down deep branches, producing a winding `289 km` route.
2. **Why A\* Beats Dijkstra:** Both `Dijkstra` and `A*` find the exact global optimum (`18.43 min`), but `A*` uses the admissible Haversine effective-speed heuristic to prune unpromising directions—reducing nodes explored by **59.7%** (`62,301` vs `154,718`) and cutting execution time nearly in half (`0.58 s` vs `1.12 s`).

---

## Interactive Map Legend (`ranchi_routes.html`)

- **Markers:**
  - **Blue Pin:** Available Ambulance Station (`#0` – `#7`)
  - **Red Pin:** Curated Hospital
  - **Green Pin:** Patient Emergency Location
- **Route Polylines (Toggleable in Top-Right Layer Control):**
  - **Solid Line:** Leg 1 (`Ambulance -> Patient`)
  - **Dashed Line:** Leg 2 (`Patient -> Hospital`)
  - **Colors:** Green = `A*`, Blue = `Dijkstra`, Orange = `BFS`, Red = `DFS`