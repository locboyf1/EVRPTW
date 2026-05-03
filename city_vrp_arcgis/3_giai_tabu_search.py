import os
import sys
import json
import numpy as np
import csv
from datetime import datetime

# Xác định thư mục gốc dựa trên vị trí file này
_THU_MUC_GOC = os.path.dirname(os.path.abspath(__file__))
if _THU_MUC_GOC not in sys.path:
    sys.path.insert(0, _THU_MUC_GOC)

from modules.tabu_search_vrp import TabuSearchVRPSolver
from giao_dien.terminal_ui import in_tieu_de, in_thong_bao

# Cấu hình
NPZ_FILE = os.path.join(_THU_MUC_GOC, "du_lieu", "cache", "ma_tran_od.npz")
KH_FILE = os.path.join(_THU_MUC_GOC, "du_lieu", "khach_hang.json")
OUT_JSON = os.path.join(_THU_MUC_GOC, "ket_qua", "tabu_ket_qua.json")
OUT_CSV = os.path.join(_THU_MUC_GOC, "ket_qua", "lich_su_so_sanh.csv")

def main():
    in_tieu_de("PHASE 2: GIẢI THUẬT TABU SEARCH")
    
    # 1. Load dữ liệu
    matrices = np.load(NPZ_FILE)
    with open(KH_FILE, "r", encoding="utf-8") as f:
        kh_json = json.load(f)
    
    # 2. Chạy Solver
    solver = TabuSearchVRPSolver(
        so_xe=17,
        tai_trong_toi_da=90,
        luong_tai_xe=26.55,
        danh_sach_khach_hang=kh_json["danh_sach_khach_hang"],
        ma_tran_chi_phi_od=matrices['cp'],
        ma_tran_khi_thai_od=matrices['kt'],
        ma_tran_thoi_gian_od=matrices['tg'] / 60.0, # Quy đổi sang phút
        toi_da_vong_lap=300
    )
    
    ket_qua = solver.giai()
    
    # 3. Lưu JSON
    os.makedirs(os.path.dirname(OUT_JSON), exist_ok=True)
    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(ket_qua, f, ensure_ascii=False, indent=4)
        
    # 4. Lưu CSV lịch sử
    header = ["Thoi_Gian", "Thanh_Pho", "So_Khach", "Chi_Phi", "Khi_Thai", "Kich_Ban"]
    file_exists = os.path.isfile(OUT_CSV)
    
    with open(OUT_CSV, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(header)
        writer.writerow([
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "Vinh City",
            len(kh_json["danh_sach_khach_hang"]),
            round(ket_qua["tong_chi_phi"], 2),
            round(ket_qua["tong_khi_thai"], 2),
            "Density (Hybrid 0.6)"
        ])
    
    in_thong_bao(f"✔ Đã lưu kết quả chi tiết vào {OUT_JSON}")
    in_thong_bao(f"✔ Đã cập nhật lịch sử so sánh vào {OUT_CSV}")

if __name__ == "__main__":
    main()
