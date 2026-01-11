import heapq
import time
import math

# --- Hàm tính khoảng cách "chim bay" (haversine) ---
def haversine(u, v, G):
    lon1, lat1 = G.nodes[u]['x'], G.nodes[u]['y']
    lon2, lat2 = G.nodes[v]['x'], G.nodes[v]['y']
    R = 6371000  # bán kính Trái Đất (m)
    dlon = math.radians(lon2 - lon1)
    dlat = math.radians(lat2 - lat1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    return R * c

# --- Thuật toán Dijkstra ---
def find_path_dijkstra(G, origin, destination):
    t0 = time.time()
    
    # Hàng đợi ưu tiên: (chi_phí_tích_lũy, nút_hiện_tại, đường_đi)
    queue = [(0, origin, [origin])]
    visited = set()
    nodes_visited_count = 0
    
    # Chi phí nhỏ nhất đến từng nút để tránh lặp vô hạn
    min_dist = {origin: 0}

    while queue:
        (d, current_node, path) = heapq.heappop(queue)
        
        if current_node in visited:
            continue
        
        visited.add(current_node)
        nodes_visited_count += 1
        
        if current_node == destination:
            elapsed = time.time() - t0
            return path, d, elapsed, nodes_visited_count
        
        # Duyệt các nút hàng xóm
        for neighbor in G[current_node]:
            # Lấy trọng số cạnh (xử lý trường hợp đa đồ thị MultiDiGraph của OSMnx)
            edge_data = G[current_node][neighbor]
            length = min([d.get('length', float('inf')) for d in edge_data.values()])
            
            if neighbor not in visited:
                new_dist = d + length
                if new_dist < min_dist.get(neighbor, float('inf')):
                    min_dist[neighbor] = new_dist
                    heapq.heappush(queue, (new_dist, neighbor, path + [neighbor]))

    return [], 0, 0, nodes_visited_count

# --- Thuật toán A* ---
def find_path_astar(G, origin, destination):
    t0 = time.time()
    
    # Hàng đợi ưu tiên: (f_score, g_score, nút_hiện_tại, đường_đi)
    # f(n) = g(n) + h(n)
    h_start = haversine(origin, destination, G)
    queue = [(h_start, 0, origin, [origin])]
    
    visited = set()
    min_dist = {origin: 0} # Lưu g_score tốt nhất
    nodes_visited_count = 0

    while queue:
        (f, g, current_node, path) = heapq.heappop(queue)
        
        if current_node in visited:
            continue
            
        visited.add(current_node)
        nodes_visited_count += 1
        
        if current_node == destination:
            elapsed = time.time() - t0
            return path, g, elapsed, nodes_visited_count
        
        for neighbor in G[current_node]:
            edge_data = G[current_node][neighbor]
            length = min([d.get('length', float('inf')) for d in edge_data.values()])
            
            if neighbor not in visited:
                new_g = g + length
                if new_g < min_dist.get(neighbor, float('inf')):
                    min_dist[neighbor] = new_g
                    new_h = haversine(neighbor, destination, G)
                    new_f = new_g + new_h
                    heapq.heappush(queue, (new_f, new_g, neighbor, path + [neighbor]))

    return [], 0, 0, nodes_visited_count

'''
# --- Hàm phụ: mô phỏng chặn đường ---
def block_road(G, lat, lon):
    nearest_edge = min(G.edges(data=True), key=lambda e: math.hypot(G.nodes[e[0]]['y'] - lat, G.nodes[e[0]]['x'] - lon))
    u, v, data = nearest_edge
    print(f"Chặn đường giữa {u} và {v}")
    G[u][v][0]["length"] *= 100  # tăng trọng số để coi như tắc đường
    return (u, v)
'''