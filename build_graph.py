import osmnx as ox

# đọc file .osm chứ không phải .pbf
G = ox.graph_from_xml("data/hbt_hk.osm", simplify=True)
print(f"Thống kê đồ thị: {len(G.nodes)} nút, {len(G.edges)} cạnh.")

ox.save_graphml(G, "data/hbt_hk.graphml")
print("Đã tạo đồ thị thành công: data/hbt_hk.graphml")
