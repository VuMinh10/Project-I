import networkx as nx
import math #Thư viện toán học: gồm sin, cos, sqrt, radians…
import time

# --- Hàm tính khoảng cách "chim bay" (haversine) giữa 2 nút ---
def haversine(u, v, G):
    lon1, lat1 = G.nodes[u]['x'], G.nodes[u]['y']
    lon2, lat2 = G.nodes[v]['x'], G.nodes[v]['y']
    R = 6371000  # bán kính Trái Đất (m)
    dlon = math.radians(lon2 - lon1)
    dlat = math.radians(lat2 - lat1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    return R * c

# --- Thuật toán A* ---
def find_path_astar(G, origin, destination):
    t0 = time.time()
    path = nx.astar_path(
        G, origin, destination,
        heuristic=lambda u, v: haversine(u, v, G),
        weight="length"
    )
    t1 = time.time()
    cost = nx.path_weight(G, path, weight="length")
    elapsed = t1 - t0
    return path, cost, elapsed

# --- Thuật toán Dijkstra ---
def find_path_dijkstra(G, origin, destination):
    t0 = time.time()
    path = nx.shortest_path(G, origin, destination, weight="length")
    t1 = time.time()
    cost = nx.path_weight(G, path, weight="length")
    elapsed = t1 - t0
    return path, cost, elapsed

'''
# --- Hàm phụ: mô phỏng chặn đường ---
def block_road(G, lat, lon):
    nearest_edge = min(G.edges(data=True), key=lambda e: math.hypot(G.nodes[e[0]]['y'] - lat, G.nodes[e[0]]['x'] - lon))
    u, v, data = nearest_edge
    print(f"🚧 Chặn đường giữa {u} và {v}")
    G[u][v][0]["length"] *= 100  # tăng trọng số để coi như tắc đường
    return (u, v)
'''