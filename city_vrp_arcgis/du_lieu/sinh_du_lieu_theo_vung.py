import json
import random
import os
import sys

# Thêm đường dẫn để import OSMnx nếu cần
try:
    import osmnx as ox
except ImportError:
    print("Lỗi: Bạn cần cài đặt osmnx (conda install osmnx) để sử dụng công cụ này.")
    sys.exit(1)

def sinh_du_lieu_thong_minh(ten_thanh_pho, so_khach=50):
    print(f"--- Đang định vị trung tâm: {ten_thanh_pho} ---")
    try:
        # Lấy tọa độ trung tâm thành phố từ OpenStreetMap
        tọa_độ = ox.geocode(ten_thanh_pho)
        lat_center, lon_center = tọa_độ
        print(f"✔ Đã tìm thấy: Lat={lat_center}, Lon={lon_center}")
    except Exception as e:
        print(f"❌ Không thể tìm thấy tọa độ cho '{ten_thanh_pho}'. Lỗi: {e}")
        return

    # Khởi tạo Kho tại tâm thành phố
    kho = {
        "ten": f"Kho trung tam {ten_thanh_pho.split(',')[0]}",
        "vi_do": lat_center,
        "kinh_do": lon_center,
        "thoi_gian_mo_cua": 0,
        "thoi_gian_dong_cua": 1440,
        "thoi_gian_boc_do": 0
    }

    customers = []
    print(f"--- Đang sinh {so_khach} khách hàng ngẫu nhiên ---")
    
    for i in range(1, so_khach + 1):
        # Sinh tọa độ ngẫu nhiên quanh tâm (khoảng 5-7km)
        # 0.01 độ kinh/vĩ tương đương khoảng 1.1km
        vi_do = lat_center + random.uniform(-0.04, 0.04)
        kinh_do = lon_center + random.uniform(-0.04, 0.04)
        
        customers.append({
            "ten": f"Khách hàng {i:02d}",
            "vi_do": vi_do,
            "kinh_do": kinh_do,
            "nhu_cau": random.randint(1, 15),
            "thoi_gian_mo_cua": random.randint(480, 600),
            "thoi_gian_dong_cua": random.randint(1000, 1200),
            "thoi_gian_boc_do": 15
        })

    data = {
        "kho_xuat_phat": kho,
        "danh_sach_khach_hang": customers
    }

    # Lưu vào file
    duong_dan = os.path.join("city_vrp_arcgis", "du_lieu", "khach_hang.json")
    with open(duong_dan, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"✅ HOÀN THÀNH: Đã cập nhật 50 khách hàng mới tại {ten_thanh_pho} vào {duong_dan}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        city = sys.argv[1]
    else:
        city = input("Nhập tên thành phố (ví dụ: Vinh City, Vietnam): ")
    
    sinh_du_lieu_thong_minh(city)
