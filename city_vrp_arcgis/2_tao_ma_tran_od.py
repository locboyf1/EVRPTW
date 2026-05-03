"""
=============================================================
PHASE 2: TẠO MA TRẬN OD (SNAP NODE + DIJKSTRA)
Nhiệm vụ: Đọc graph + khach_hang.json, snap điểm vào node,
           chạy Dijkstra tạo 4 ma trận, áp dụng hệ số Hybrid.
Input:     du_lieu/cache/do_thi_osm.pkl + du_lieu/khach_hang.json
Output:    du_lieu/cache/ma_tran_od.npz
=============================================================
"""

import os
import sys
import pickle
import json
import numpy as np

# Xác định thư mục gốc dựa trên vị trí file này
_THU_MUC_GOC = os.path.dirname(os.path.abspath(__file__))
if _THU_MUC_GOC not in sys.path:
    sys.path.insert(0, _THU_MUC_GOC)

from modules.dijkstra_logic import snap_diem_vao_do_thi, tao_ma_tran_od_bang_dijkstra
from giao_dien.terminal_ui import in_tieu_de, in_thong_bao, in_canh_bao

# Cấu hình
CACHE_OSM = os.path.join(_THU_MUC_GOC, "du_lieu", "cache", "do_thi_osm.pkl")
KH_FILE = os.path.join(_THU_MUC_GOC, "du_lieu", "khach_hang.json")
KHI_THAI_FILE = os.path.join(_THU_MUC_GOC, "du_lieu", "du_lieu_khi_thai.json")
XE_FILE = os.path.join(_THU_MUC_GOC, "du_lieu", "cau_hinh_xe.json")
OUTPUT_NPZ = os.path.join(_THU_MUC_GOC, "du_lieu", "cache", "ma_tran_od.npz")
LUONG_TAI_XE = 26.55
HE_SO_HYBRID = 0.6

def main():
    in_tieu_de("PHASE 2: SNAP NODE + TẠO MA TRẬN OD (DIJKSTRA)")
    
    # 1. Load graph từ cache
    with open(CACHE_OSM, "rb") as f:
        data = pickle.load(f)
    G = data["graph"]
    dung_osm = data["dung_osm"]
    in_thong_bao(f"✔ Đã load đồ thị: {len(G.nodes):,} nút")
    
    # 2. Load khách hàng
    with open(KH_FILE, "r", encoding="utf-8") as f:
        kh_json = json.load(f)
    tat_ca_diem = [kh_json["kho_xuat_phat"]] + kh_json["danh_sach_khach_hang"]
    in_thong_bao(f"✔ Đã load {len(tat_ca_diem) - 1} khách hàng + 1 kho")
    
    # 3. Snap điểm vào node đồ thị
    in_thong_bao("Đang snap các điểm vào mạng lưới đường phố...")
    nodes_id = snap_diem_vao_do_thi(G, tat_ca_diem, dung_osmnx=dung_osm)
    in_thong_bao(f"✔ Đã snap {len(nodes_id)} điểm vào node đồ thị")
    
    # 4. Load dữ liệu khí thải và xe
    with open(KHI_THAI_FILE, "r", encoding="utf-8") as f:
        kt_json = json.load(f)
    with open(XE_FILE, "r", encoding="utf-8") as f:
        xe_json = json.load(f)
    
    bang_moves = {int(k): v for k, v in kt_json["bang_moves"].items()}
    xe_mau = xe_json["danh_sach_xe"][0]
    
    # 5. Chạy Dijkstra
    cp, kt, tg, km = tao_ma_tran_od_bang_dijkstra(G, nodes_id, xe_mau, LUONG_TAI_XE, bang_moves)
    
    # 6. Áp dụng Hybrid cho khí thải
    kt_final = kt * HE_SO_HYBRID
    in_thong_bao(f"✔ Đã áp dụng hệ số Hybrid: ×{HE_SO_HYBRID}")
    
    # 7. Lưu ma trận
    os.makedirs(os.path.dirname(OUTPUT_NPZ), exist_ok=True)
    np.savez(OUTPUT_NPZ, cp=cp, kt=kt_final, tg=tg, km=km)
    in_thong_bao(f"✔ Đã lưu 4 ma trận OD → {OUTPUT_NPZ}")

if __name__ == "__main__":
    main()
