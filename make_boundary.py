import geopandas as gpd
from shapely.geometry import box
import os

# Tạo thư mục data nếu chưa có
os.makedirs("data", exist_ok=True)

# osmium extract -b 105.83,21.00,105.87,21.05
min_lon, min_lat, max_lon, max_lat = 105.83, 21.00, 105.87, 21.05

geom = box(min_lon, min_lat, max_lon, max_lat)

# Tạo GeoDataFrame
gdf = gpd.GeoDataFrame(index=[0], geometry=[geom], crs="EPSG:4326")

# Lưu file
gdf.to_file("data/boundary.geojson", driver="GeoJSON")
print(f"Đã tạo boundary.geojson: Hình vuông chuẩn ({min_lon}, {min_lat}) - ({max_lon}, {max_lat})")