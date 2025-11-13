# server.py
from flask import Flask, render_template, request
import osmnx as ox
import folium
from pathfinding import find_path_astar, find_path_dijkstra
import os

app = Flask(__name__, template_folder='templates')

# load graph once
if not os.path.exists("data/hbt_hk.graphml"):
    raise FileNotFoundError("Run build_graph.py first to create data/hbt.graphml")
G = ox.load_graphml("data/hbt_hk.graphml")

@app.route("/")
def index():
    if not os.path.exists("templates/map_interactive.html"):
        return "<h3>map_interactive.html not found. Run main_interactive.py</h3>"
    return render_template("map_interactive.html")

@app.route("/route")
def route():
    try:
        start_lat = float(request.args.get("start_lat"))
        start_lon = float(request.args.get("start_lon"))
        end_lat = float(request.args.get("end_lat"))
        end_lon = float(request.args.get("end_lon"))
    except Exception as e:
        return f"<h3>Invalid parameters: {e}</h3>"

    print(f"➡ Request: start=({start_lat},{start_lon}) end=({end_lat},{end_lon})")

    orig = ox.distance.nearest_nodes(G, start_lon, start_lat)
    dest = ox.distance.nearest_nodes(G, end_lon, end_lat)

    path_a, cost_a, t_a = find_path_astar(G, orig, dest)
    path_d, cost_d, t_d = find_path_dijkstra(G, orig, dest)

    # convert node lists to lat/lon coords
    def nodes_to_latlon(G, path):
        return [(G.nodes[n]['y'], G.nodes[n]['x']) for n in path]

    coords_a = nodes_to_latlon(G, path_a)
    coords_d = nodes_to_latlon(G, path_d)

    # center map at midpoint
    center = [(start_lat + end_lat) / 2.0, (start_lon + end_lon) / 2.0]
    m = folium.Map(location=center, zoom_start=15, tiles="OpenStreetMap")

    # draw base road network light (optional; comment out if slow)
    for u, v, data in G.edges(data=True):
        if "geometry" in data:
            pts = [(p[1], p[0]) for p in data["geometry"].coords]
            folium.PolyLine(pts, color="lightgray", weight=1, opacity=0.25).add_to(m)

    # draw boundary (nếu có file boundary.geojson)
    import geopandas as gpd
    if os.path.exists("data/boundary.geojson"):
        boundary = gpd.read_file("data/boundary.geojson")
        folium.GeoJson(
            boundary.__geo_interface__,
            style_function=lambda x: {"color": "green", "weight": 3, "fillOpacity": 0.0}
        ).add_to(m)

    # draw Dijkstra (blue) - luôn vẽ dưới cùng
    if coords_d and len(coords_d) > 1:
        folium.PolyLine(
            coords_d, color='blue', weight=6, opacity=0.5, tooltip="Dijkstra"
        ).add_to(m)
    else:
        print("⚠️ Dijkstra path empty or invalid")

    # draw A* (red) - vẽ chồng lên để phân biệt
    if coords_a and len(coords_a) > 1:
        folium.PolyLine(
            coords_a, color='red', weight=3, opacity=0.9, tooltip="A*"
        ).add_to(m)
    else:
        print("⚠️ A* path empty or invalid")

    # markers
    folium.Marker([start_lat, start_lon], popup="Start", icon=folium.Icon(color='green')).add_to(m)
    folium.Marker([end_lat, end_lon], popup="End", icon=folium.Icon(color='red')).add_to(m)

    # add metrics box (HTML) as Float pane
    html_metrics = f"""
    <div style="background: white; padding:8px; border-radius:6px; box-shadow:2px 2px 6px rgba(0,0,0,0.3);">
      <h4 style="margin:0 0 6px 0">Kết quả tìm đường</h4>
      <table style="font-size:13px">
        <tr><td><b>A*</b></td><td>{cost_a:.2f} m</td><td>{t_a:.4f} s</td></tr>
        <tr><td><b>Dijkstra</b></td><td>{cost_d:.2f} m</td><td>{t_d:.4f} s</td></tr>
      </table>
      <div style="margin-top:6px"><button onclick="window.location.href='/'">⟵ Quay lại</button></div>
    </div>
    """
    from branca.element import MacroElement, Element
    metrics = Element(f"""<div id="metrics" style="position: fixed; top: 10px; left: 10px; z-index: 9999;">{html_metrics}</div>""")
    m.get_root().html.add_child(metrics)

    # save and render
    os.makedirs("templates", exist_ok=True)
    m.save("templates/route_result.html")
    print(f"   A*: {cost_a:.1f}m {t_a:.4f}s | Dijkstra: {cost_d:.1f}m {t_d:.4f}s")
    return render_template("route_result.html")

if __name__ == "__main__":
    print("🚀 Server starting at http://127.0.0.1:5000")
    app.run(debug=True)



