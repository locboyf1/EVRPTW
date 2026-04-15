import json
import random
import os
import sys

# Khong su dung io de tranh xung dot tren Terminal Windows
try:
    import osmnx as ox
except ImportError:
    print("Loi: Ban can cai dat osmnx (conda install osmnx) de su dung cong cu nay.")
    sys.exit(1)

def sinh_du_lieu_thong_minh(ten_thanh_pho, so_khach=50):
    print(f"--- Dang dinh vi trung tam: {ten_thanh_pho} ---")
    try:
        # Lay toa do trung tam thanh pho tu OpenStreetMap
        toa_do = ox.geocode(ten_thanh_pho)
        lat_center, lon_center = toa_do
        print(f"OK - Da tim thay: Lat={lat_center}, Lon={lon_center}")
    except Exception as e:
        print(f"ERROR - Khong the tim thay toa do cho '{ten_thanh_pho}'. Loi: {e}")
        return

    # Khoi tao Kho tai tam thanh pho
    kho = {
        "ten": f"Kho trung tam {ten_thanh_pho.split(',')[0]}",
        "vi_do": lat_center,
        "kinh_do": lon_center,
        "thoi_gian_mo_cua": 0,
        "thoi_gian_dong_cua": 1440,
        "thoi_gian_boc_do": 0
    }

    customers = []
    print(f"--- Dang sinh {so_khach} khach hang ngau nhien ---")
    
    for i in range(1, so_khach + 1):
        # Sinh toa do ngau nhien quanh tam (khoang 5-7km)
        vi_do = lat_center + random.uniform(-0.04, 0.04)
        kinh_do = lon_center + random.uniform(-0.04, 0.04)
        
        # Ca sang: 0 - 360 phut (theo yeu cau Blueprint)
        ready_time = random.randint(0, 300)
        due_date = ready_time + 30 # Do rong Time Window co dinh 30 phut
        
        customers.append({
            "ten": f"Khach hang {i:02d}",
            "vi_do": vi_do,
            "kinh_do": kinh_do,
            "nhu_cau": random.randint(1, 15), # Nhu cau 1-15 don vi
            "thoi_gian_mo_cua": ready_time,
            "thoi_gian_dong_cua": due_date,
            "thoi_gian_boc_do": 10 # Co dinh 10 phut
        })

    data = {
        "kho_xuat_phat": kho,
        "danh_sach_khach_hang": customers
    }

    # Luu vao file
    duong_dan = os.path.join("city_vrp_arcgis", "du_lieu", "khach_hang.json")
    with open(duong_dan, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"DONE - Da cap nhat 50 khach hang moi tai {ten_thanh_pho} vao {duong_dan}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        city = sys.argv[1]
    else:
        city = input("Nhap ten thanh pho (vd: Vinh, Nghe An, Vietnam): ")
    
    sinh_du_lieu_thong_minh(city)
