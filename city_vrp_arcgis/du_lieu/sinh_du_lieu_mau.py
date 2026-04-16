import csv
import random
import os

FILE_PATH = "city_vrp_arcgis/du_lieu/lich_su_chay.csv"

def sinh_du_lieu_mau():
    # Đảm bảo thư mục tồn tại
    os.makedirs(os.path.dirname(FILE_PATH), exist_ok=True)
    
    header = ["Thoi_Gian", "Thanh_Pho", "So_Khach", "Alpha", "Beta", "Chi_Phi", "Khi_Thai", "Kich_Ban"]
    
    data_points = []
    
    # 1. Kịch bản: Base Case (Cơ sở)
    for _ in range(15):
        so_khach = 50
        co2_per_order = random.uniform(4.0, 6.0)
        usd_per_order = co2_per_order * 3.7 + random.uniform(-1, 1)
        data_points.append([
            "2026-04-16 08:00:00", "Vinh, Viet Nam", so_khach, 0.5, 0.5,
            round(usd_per_order * so_khach, 2),
            round(co2_per_order * so_khach, 2),
            "Base Case"
        ])

    # 2. Kịch bản: Time Window
    for _ in range(15):
        so_khach = 50
        co2_per_order = random.uniform(3.0, 5.0)
        usd_per_order = co2_per_order * 4.2 + random.uniform(2, 4)
        data_points.append([
            "2026-04-16 09:00:00", "Vinh", so_khach, 0.5, 0.5,
            round(usd_per_order * so_khach, 2),
            round(co2_per_order * so_khach, 2),
            "Time Window"
        ])

    # 3. Kịch bản: Density
    for _ in range(15):
        so_khach = 100
        co2_per_order = random.uniform(1.5, 3.5)
        usd_per_order = co2_per_order * 3.1 + random.uniform(-1, 0)
        data_points.append([
            "2026-04-16 10:00:00", "Vinh", so_khach, 0.5, 0.5,
            round(usd_per_order * so_khach, 2),
            round(co2_per_order * so_khach, 2),
            "Density"
        ])

    with open(FILE_PATH, mode='w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(data_points)
    
    print(f"--- Da tao thanh cong 45 diem du lieu mau tai {FILE_PATH} ---")

if __name__ == "__main__":
    sinh_du_lieu_mau()
