# main_interactive.py
import osmnx as ox
import folium
import geopandas as gpd
import os

# load graph + boundary
G = ox.load_graphml("data/hbt_hk.graphml")
boundary = gpd.read_file("data/boundary.geojson")

center_lat = float(boundary.geometry.centroid.y[0])
center_lon = float(boundary.geometry.centroid.x[0])

m = folium.Map(location=[center_lat, center_lon], zoom_start=15, tiles="OpenStreetMap")

# draw boundary
folium.GeoJson(boundary.__geo_interface__, style_function=lambda x: {
    "color": "green", "weight": 3, "fillOpacity": 0.0
}).add_to(m)

# draw road network (light)
for u, v, data in G.edges(data=True):
    if "geometry" in data:
        pts = [(p[1], p[0]) for p in data["geometry"].coords]
        folium.PolyLine(pts, color="lightgray", weight=1, opacity=0.35).add_to(m)

# inject robust JS: find folium map var, attach click, add "Reset" button
map_var = m.get_name()

custom_js = f"""
<script>
console.log("interactive map loaded");
document.addEventListener("DOMContentLoaded", function() {{
    // find the map object created by folium
    var mapObj = null;
    for (var k in window) {{
        if (k.startsWith("map_")) {{
            mapObj = window[k];
            break;
        }}
    }}
    if (!mapObj) {{
        console.error("Map object not found.");
        return;
    }}
    var points = [];

    function resetClicks() {{
        points = [];
        // remove all non-tile layers (markers/polylines) by reloading page or removing specific layers if needed
        window.location.href = "/";
    }}

    // create a simple control button
    var resetControl = L.control({{position: 'topright'}});
    resetControl.onAdd = function(map) {{
        var div = L.DomUtil.create('div', 'leaflet-bar leaflet-control leaflet-control-custom');
        div.style.backgroundColor = 'white';
        div.style.padding = '3px';
        div.style.cursor = 'pointer';
        div.title = 'Reset chọn điểm';
        div.innerHTML = '🔁 Reset';
        div.onclick = function() {{ resetClicks(); }};
        return div;
    }};
    resetControl.addTo(mapObj);

    mapObj.on('click', function(e) {{
        console.log('map click', e.latlng);
        var lat = e.latlng.lat;
        var lon = e.latlng.lng;
        points.push([lat, lon]);
        L.circleMarker([lat, lon], {{radius:6, color: points.length===1 ? 'green' : 'red', fill:true}}).addTo(mapObj);
        if (points.length === 2) {{
            var url = '/route?start_lat=' + points[0][0] + '&start_lon=' + points[0][1] +
                      '&end_lat=' + points[1][0] + '&end_lon=' + points[1][1];
            console.log('redirect to', url);
            window.location.href = url;
        }}
    }});
}});
</script>
"""

# Save template
os.makedirs("templates", exist_ok=True)
html = m.get_root().render().replace("</body>", custom_js + "</body>")
with open("templates/map_interactive.html", "w", encoding="utf-8") as f:
    f.write(html)

print("✅ templates/map_interactive.html created. Run server.py and open http://127.0.0.1:5000")


