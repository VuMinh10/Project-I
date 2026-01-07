Môi trường: anaconda  
Các thư viện python cần tải: osmnx, folium, geopandas, networkx, flask, shapely  
Các bước chạy chương trình:  
B1: Tải thư mục data tại link: https://drive.google.com/drive/folders/1VmASPZ6HG4v3hNxuG04fMX0oRI5cX4x0?usp=drive_link  
B2: Trước khi khởi động ứng dụng Web, cần chạy các tập lệnh để xây dựng cấu trúc đồ thị. Chạy lần lượt các lệnh sau:
+ python make_boundary.py
+ python build_graph.py
+ python main_interactive.py
 
B3: Khởi chạy server và sử dụng:
+ Chạy lệnh: python server.py
+ Truy cập http://127.0.0.1:5000/ trên trình duyệt
