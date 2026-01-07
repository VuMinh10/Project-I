from flask import Flask, render_template, request
import osmnx as ox
import folium
import geopandas as gpd
from shapely.geometry import Point
from pathfinding import find_path_astar, find_path_dijkstra
import os
import networkx as nx

app = Flask(__name__, template_folder='templates')

# --- KHỞI TẠO DỮ LIỆU ---
print("⏳ Đang khởi động Server...")
if not os.path.exists("data/hbt_hk.graphml"):
    raise FileNotFoundError("Thiếu file data/hbt_hk.graphml!")

G = ox.load_graphml("data/hbt_hk.graphml")

# Load boundary và giữ trong biến toàn cục để kiểm tra
boundary_gdf = None
if os.path.exists("data/boundary.geojson"):
    boundary_gdf = gpd.read_file("data/boundary.geojson")

print("✅ Server đã sẵn sàng!")

@app.route("/")
def index():
    if not os.path.exists("templates/map_interactive.html"):
        return "<h3>Lỗi: Hãy chạy main_interactive.py trước!</h3>"
    return render_template("map_interactive.html")

@app.route("/route")
def route():
    try:
        start_lat = float(request.args.get("start_lat"))
        start_lon = float(request.args.get("start_lon"))
        end_lat = float(request.args.get("end_lat"))
        end_lon = float(request.args.get("end_lon"))

        # --- KIỂM TRA ĐIỂM CÓ NẰM TRONG VÙNG KHÔNG ---
        if boundary_gdf is not None:
            # Tạo điểm Shapely
            p_start = Point(start_lon, start_lat)
            p_end = Point(end_lon, end_lat)
            
            # Kiểm tra: boundary có chứa điểm đó không?
            # Lấy geometry đầu tiên (vì boundary chỉ có 1 hình vuông)
            poly = boundary_gdf.geometry.iloc[0]
            
            if not poly.contains(p_start) or not poly.contains(p_end):
                return """
                <div style="text-align:center; padding: 20px; font-family: sans-serif;">
                    <h2 style="color:red;">❌ Điểm chọn nằm ngoài vùng dữ liệu!</h2>
                    <p>Hệ thống chỉ có dữ liệu trong khung màu xanh.</p>
                    <button onclick="window.location.href='/'" style="padding:10px;">Quay lại chọn lại</button>
                </div>
                """

        # Nếu hợp lệ thì mới tìm đường
        orig = ox.distance.nearest_nodes(G, start_lon, start_lat)
        dest = ox.distance.nearest_nodes(G, end_lon, end_lat)

        path_a, cost_a, t_a = find_path_astar(G, orig, dest)
        path_d, cost_d, t_d = find_path_dijkstra(G, orig, dest)

        coords_a = [(G.nodes[n]['y'], G.nodes[n]['x']) for n in path_a]
        coords_d = [(G.nodes[n]['y'], G.nodes[n]['x']) for n in path_d]

        center = [(start_lat + end_lat) / 2.0, (start_lon + end_lon) / 2.0]
        m = folium.Map(location=center, zoom_start=15, tiles="OpenStreetMap")

        # Vẽ Boundary
        if boundary_gdf is not None:
             folium.GeoJson(
                boundary_gdf.__geo_interface__,
                style_function=lambda x: {"color": "green", "weight": 2, "fillOpacity": 0.0, "dashArray": "5, 5"}
            ).add_to(m)

        # Vẽ đường đi
        folium.PolyLine(coords_d, color='blue', weight=8, opacity=0.4, tooltip=f"Dijkstra: {cost_d:.1f}m").add_to(m)
        folium.PolyLine(coords_a, color='red', weight=4, opacity=0.8, tooltip=f"A*: {cost_a:.1f}m").add_to(m)

        folium.Marker([start_lat, start_lon], popup="Start", icon=folium.Icon(color='green', icon='play')).add_to(m)
        folium.Marker([end_lat, end_lon], popup="End", icon=folium.Icon(color='red', icon='stop')).add_to(m)

        # Bảng kết quả
        html_metrics = f"""
        <div style="background-color: rgba(255, 255, 255, 0.9); padding: 15px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
            <h4 style="margin: 0 0 10px 0;">📊 Kết quả</h4>
            <div style="color: red;"><b>A*</b>: {cost_a:.1f} m ({t_a:.4f}s)</div>
            <div style="color: blue;"><b>Dijkstra</b>: {cost_d:.1f} m ({t_d:.4f}s)</div>
            <br>
            <button onclick="window.location.href='/'">⟵ Chọn lại</button>
        </div>
        """
        m.get_root().html.add_child(folium.Element(f'<div style="position: fixed; top: 20px; left: 50px; z-index: 9999;">{html_metrics}</div>'))

        m.save("templates/route_result.html")
        return render_template("route_result.html")

    except nx.NetworkXNoPath:
        return "<h3>❌ Không tìm thấy đường đi (Khu vực bị ngăn cách)!</h3><a href='/'>Quay lại</a>"
    except Exception as e:
        return f"<h3>❌ Lỗi: {e}</h3><a href='/'>Quay lại</a>"

if __name__ == "__main__":
    app.run(debug=True, port=5000)