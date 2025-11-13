import geopandas as gpd
from shapely.geometry import box

# Tạo bounding box
min_lon, min_lat, max_lon, max_lat = 105.83, 20.99, 105.88, 21.05
geom = box(min_lon, min_lat, max_lon, max_lat)

# Tạo GeoDataFrame
gdf = gpd.GeoDataFrame(index=[0], geometry=[geom], crs="EPSG:4326")

# Lưu
gdf.to_file("data/boundary.geojson", driver="GeoJSON")
print("✅ boundary.geojson created.")
