from flask import Flask, render_template, request
import osmnx as ox
import folium
import geopandas as gpd
from shapely.geometry import Point

from pathfinding import find_path_astar, find_path_dijkstra
import os
import networkx as nx

from geopy.geocoders import Nominatim

app = Flask(__name__, template_folder='templates')

# --- Khởi tạo Geocoder ---
geolocator = Nominatim(user_agent="routing_app_text_function")

# --- Hàm lấy toạ độ chi tiết bám theo đường cong ---
def get_path_geometry(G, path):
    if not path:
        return []
        
    route_coords = []
    
    # Thêm toạ độ điểm xuất phát đầu tiên
    first_node = G.nodes[path[0]]
    route_coords.append((first_node['y'], first_node['x']))
    
    for i in range(len(path) - 1):
        u = path[i]
        v = path[i+1]
        
        # Lấy dữ liệu cạnh nối giữa u và v
        # Vì là MultiDiGraph (có thể có nhiều đường nối 2 điểm) nên lấy tất cả
        edges = G.get_edge_data(u, v)
        
        if edges:
            # Chọn cạnh có độ dài ngắn nhất (logic giống thuật toán tìm đường)
            best_key = min(edges, key=lambda k: edges[k].get('length', float('inf')))
            data = edges[best_key]
            
            if 'geometry' in data:
                # Nếu cạnh có thuộc tính geometry (đường cong)
                # data['geometry'] là object LineString của shapely
                # Tách toạ độ x (lon) và y (lat)
                xs, ys = data['geometry'].xy
                
                # Zip lại thành list (lat, lon) để folium hiểu
                # Bỏ điểm đầu tiên [1:] vì nó trùng với điểm cuối của cạnh trước
                edge_coords = list(zip(ys, xs))
                route_coords.extend(edge_coords[1:])
            else:
                # Nếu cạnh thẳng (không có geometry), chỉ cần thêm điểm đích v
                node_v = G.nodes[v]
                route_coords.append((node_v['y'], node_v['x']))
                
    return route_coords

def resolve_address(address_text):
    try:
        search_query = f"{address_text}, Hà Nội, Việt Nam"
        location = geolocator.geocode(search_query)
        if location:
            return location.latitude, location.longitude
        return None
    except Exception as e:
        print(f"Lỗi Geocoding: {e}")
        return None

# --- KHỞI TẠO DỮ LIỆU ---
print("Đang khởi động Server...")
if not os.path.exists("data/hbt_hk.graphml"):
    print("xxx Cảnh báo: Không tìm thấy data/hbt_hk.graphml. Vui lòng chạy build_graph.py trước.")
else:
    G = ox.load_graphml("data/hbt_hk.graphml")

# Load boundary
boundary_gdf = None
if os.path.exists("data/boundary.geojson"):
    boundary_gdf = gpd.read_file("data/boundary.geojson")

print("Server đã sẵn sàng!")

@app.route("/")
def index():
    if not os.path.exists("templates/map_interactive.html"):
        return "<h3>Lỗi: Hãy chạy main_interactive.py trước!</h3>"
    return render_template("map_interactive.html")

@app.route("/search_address")
def search_address():
    start_str = request.args.get("start_str")
    end_str = request.args.get("end_str")
    
    start_coord = resolve_address(start_str)
    end_coord = resolve_address(end_str)
    
    if not start_coord:
        return f"<h3>Không tìm thấy địa chỉ: {start_str}</h3><a href='/'>Quay lại</a>"
    if not end_coord:
        return f"<h3>Không tìm thấy địa chỉ: {end_str}</h3><a href='/'>Quay lại</a>"
        
    return redirect(url_for('route', 
                            start_lat=start_coord[0], start_lon=start_coord[1],
                            end_lat=end_coord[0], end_lon=end_coord[1]))

@app.route("/route")
def route():
    try:
        start_lat = float(request.args.get("start_lat"))
        start_lon = float(request.args.get("start_lon"))
        end_lat = float(request.args.get("end_lat"))
        end_lon = float(request.args.get("end_lon"))

        # Kiểm tra điểm có nằm trong vùng không
        if boundary_gdf is not None:
            p_start = Point(start_lon, start_lat)
            p_end = Point(end_lon, end_lat)
            poly = boundary_gdf.geometry.iloc[0]
            
            if not poly.contains(p_start) or not poly.contains(p_end):
                return """
                <div style="text-align:center; padding: 20px; font-family: sans-serif;">
                    <h2 style="color:red;">Điểm chọn nằm ngoài vùng dữ liệu!</h2>
                    <p>Hệ thống chỉ có dữ liệu trong khung màu xanh.</p>
                    <button onclick="window.location.href='/'" style="padding:10px;">Quay lại chọn lại</button>
                </div>
                """

        # Tìm node gần nhất
        orig = ox.distance.nearest_nodes(G, start_lon, start_lat)
        dest = ox.distance.nearest_nodes(G, end_lon, end_lat)

        # Gọi thuật toán
        path_a, cost_a, t_a, visited_a = find_path_astar(G, orig, dest)
        path_d, cost_d, t_d, visited_d = find_path_dijkstra(G, orig, dest)

        #coords_a = [(G.nodes[n]['y'], G.nodes[n]['x']) for n in path_a]
        #coords_d = [(G.nodes[n]['y'], G.nodes[n]['x']) for n in path_d]
        coords_a = get_path_geometry(G, path_a)
        coords_d = get_path_geometry(G, path_d)

        center = [(start_lat + end_lat) / 2.0, (start_lon + end_lon) / 2.0]
        m = folium.Map(location=center, zoom_start=15, tiles="OpenStreetMap")

        # Vẽ Boundary
        if boundary_gdf is not None:
             folium.GeoJson(
                boundary_gdf.__geo_interface__,
                name="Ranh giới",
                style_function=lambda x: {"color": "green", "weight": 2, "fillOpacity": 0.0, "dashArray": "5, 5"}
            ).add_to(m)

        # Layer Control Group
        fg_dijkstra = folium.FeatureGroup(name="Dijkstra (Xanh)", show=False)
        folium.PolyLine(coords_d, color='blue', weight=8, opacity=0.5, tooltip=f"Dijkstra: {cost_d:.1f}m").add_to(fg_dijkstra)
        fg_dijkstra.add_to(m)

        fg_astar = folium.FeatureGroup(name="A* (Đỏ)", show=True)
        folium.PolyLine(coords_a, color='red', weight=4, opacity=0.8, tooltip=f"A*: {cost_a:.1f}m").add_to(fg_astar)
        fg_astar.add_to(m)

        folium.LayerControl(collapsed=False).add_to(m)
        folium.Marker([start_lat, start_lon], popup="Start", icon=folium.Icon(color='green', icon='play')).add_to(m)
        folium.Marker([end_lat, end_lon], popup="End", icon=folium.Icon(color='red', icon='stop')).add_to(m)

        # Cập nhập bảng kết quả
        html_metrics = f"""
        <div style="background-color: rgba(255, 255, 255, 0.95); padding: 15px; border-radius: 8px; box-shadow: 0 4px 10px rgba(0,0,0,0.2); font-family: sans-serif; min-width: 250px;">
            <h4 style="margin: 0 0 10px 0; border-bottom: 1px solid #ccc; padding-bottom: 5px;">So sánh hiệu năng</h4>
            
            <div style="margin-bottom: 10px;">
                <b style="color: #d63031;">A* Algorithm</b><br>
                • Quãng đường: {cost_a:.1f} m<br>
                • Thời gian: {t_a:.4f} s<br>
                • Nút đã duyệt: <b>{visited_a}</b>
            </div>
            
            <div style="margin-bottom: 15px;">
                <b style="color: #0984e3;">Dijkstra Algorithm</b><br>
                • Quãng đường: {cost_d:.1f} m<br>
                • Thời gian: {t_d:.4f} s<br>
                • Nút đã duyệt: <b>{visited_d}</b>
            </div>
            
            <button onclick="window.location.href='/'" style="width: 100%; padding: 8px; background: #2d3436; color: white; border: none; border-radius: 4px; cursor: pointer;">
                ⟵ Chọn điểm khác
            </button>
        </div>
        """
        m.get_root().html.add_child(folium.Element(f'<div style="position: fixed; top: 70px; left: 20px; z-index: 9999;">{html_metrics}</div>'))

        m.save("templates/route_result.html")
        return render_template("route_result.html")

    except nx.NetworkXNoPath:
        return "<h3>X Không tìm thấy đường đi!</h3><a href='/'>Quay lại</a>"
    except Exception as e:
        return f"<h3>X Lỗi: {e}</h3><a href='/'>Quay lại</a>"

if __name__ == "__main__":
    app.run(debug=True, port=5000)