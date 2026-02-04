import osmnx as ox
import folium
import geopandas as gpd
import os

def create_base_map():
    print("Đang tạo bản đồ tương tác...")
    
    # Load boundary để lấy tâm bản đồ
    center_lat, center_lon = 21.01, 105.85 # Mặc định
    boundary_json = None
    
    if os.path.exists("data/boundary.geojson"):
        boundary_gdf = gpd.read_file("data/boundary.geojson")
        centroid = boundary_gdf.geometry.centroid
        center_lat, center_lon = float(centroid.y[0]), float(centroid.x[0])
        boundary_json = boundary_gdf.__geo_interface__
    
    # Tạo map
    m = folium.Map(location=[center_lat, center_lon], zoom_start=14, tiles="OpenStreetMap")

    # Vẽ Boundary (Viền xanh)
    if boundary_json:
        folium.GeoJson(
            boundary_json,
            name="Ranh giới khu vực",
            style_function=lambda x: {
                "color": "#006400", 
                "weight": 3, 
                #"fillColor": "#00FF00",
                #"fillOpacity": 0.1,
                "fill": False, 
                "dashArray": "5, 5"
            }
        ).add_to(m)

    # --- HTML UI FORM NHẬP ĐỊA CHỈ ---
    search_html = """
    <div style="
        position: fixed; 
        top: 20px; left: 50px; 
        width: 300px;
        background-color: white; 
        z-index: 9999; 
        padding: 15px; 
        border-radius: 8px; 
        box-shadow: 0 0 15px rgba(0,0,0,0.2);
        font-family: Arial, sans-serif;">
        
        <h4 style="margin-top:0;">Tìm đường</h4>
        
        <div style="margin-bottom: 10px;">
            <label style="font-size: 12px; font-weight: bold;">Điểm đi (Địa chỉ/Tên):</label>
            <input type="text" id="start_addr" placeholder="VD: Nhà hát lớn Hà Nội" 
                   style="width: 100%; padding: 5px; box-sizing: border-box; margin-top: 5px;">
        </div>
        
        <div style="margin-bottom: 15px;">
            <label style="font-size: 12px; font-weight: bold;">Điểm đến:</label>
            <input type="text" id="end_addr" placeholder="VD: Hồ Hoàn Kiếm" 
                   style="width: 100%; padding: 5px; box-sizing: border-box; margin-top: 5px;">
        </div>
        
        <button onclick="searchByAddress()" style="
            width: 100%; 
            padding: 8px; 
            background-color: #007bff; 
            color: white; 
            border: none; 
            border-radius: 4px; 
            cursor: pointer; 
            font-weight: bold;">
            Tìm đường ngay
        </button>
        
        <hr style="margin: 15px 0; border: 0; border-top: 1px solid #eee;">
        
        <small style="color: #666;">* Hoặc bấm trực tiếp 2 điểm trên bản đồ</small>
    </div>
    """
    m.get_root().html.add_child(folium.Element(search_html))

    # --- JAVASCRIPT ---
    custom_js = """
    <script>
    document.addEventListener("DOMContentLoaded", function() {
        var mapObj = null;
        for (var k in window) {
            if (k.startsWith("map_")) { mapObj = window[k]; break; }
        }
        
        var points = [];
        var markers = [];

        function resetClicks() {
            points = [];
            markers.forEach(function(mk) { mapObj.removeLayer(mk); });
            markers = [];
            console.log("Đã reset điểm chọn!");
        }

        var resetControl = L.control({position: 'topright'});
        resetControl.onAdd = function(map) {
            var div = L.DomUtil.create('div', 'leaflet-bar leaflet-control leaflet-control-custom');
            div.style.backgroundColor = 'white'; 
            div.style.padding = '5px 10px'; 
            div.style.cursor = 'pointer'; 
            div.style.fontWeight = 'bold';
            div.style.border = '2px solid #ccc';
            div.innerHTML = '🔁 Chọn lại';
            
            // Ngăn chặn sự kiện click trôi xuống bản đồ
            L.DomEvent.disableClickPropagation(div);
            
            // Bắt sự kiện click
            div.onclick = function(e) {
                L.DomEvent.stopPropagation(e); // Chặn lan truyền
                resetClicks();
            };
            
            return div;
        };
        resetControl.addTo(mapObj);

        mapObj.on('click', function(e) {
            var lat = e.latlng.lat;
            var lon = e.latlng.lng;
            points.push([lat, lon]);
            
            var color = points.length === 1 ? 'green' : 'red';
            var mk = L.circleMarker([lat, lon], {radius:8, color: color, fill:true, fillOpacity:1}).addTo(mapObj);
            markers.push(mk);

            if (points.length === 2) {
                var popup = L.popup()
                    .setLatLng([lat, lon])
                    .setContent("Đang tìm đường...")
                    .openOn(mapObj);
                
                setTimeout(function(){
                    var url = '/route?start_lat=' + points[0][0] + '&start_lon=' + points[0][1] +
                              '&end_lat=' + points[1][0] + '&end_lon=' + points[1][1];
                    window.location.href = url;
                }, 100);
            }
        });
    });
    </script>
    """
    
    m.get_root().html.add_child(folium.Element(custom_js))

    os.makedirs("templates", exist_ok=True)
    m.save("templates/map_interactive.html")

if __name__ == "__main__":
    create_base_map()