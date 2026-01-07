import osmnx as ox

# đọc file .osm chứ không phải .pbf
G = ox.graph_from_xml("data/hbt_hk.osm", simplify=False)

ox.save_graphml(G, "data/hbt_hk.graphml")
print("✅ Đã tạo đồ thị thành công: data/hbt_hk.graphml")
