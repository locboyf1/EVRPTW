"""
=============================================================
PHASE 1: TẢI BẢN ĐỒ ĐƯỜNG PHỐ (OSMnx)
Nhiệm vụ: Tải đồ thị đường phố thực tế, lưu cache.
           KHÔNG snap node — vì khách hàng chưa được sinh.
Output:    du_lieu/cache/do_thi_osm.pkl
=============================================================
"""

import os
import sys
import pickle

# Xác định thư mục gốc dựa trên vị trí file này
_THU_MUC_GOC = os.path.dirname(os.path.abspath(__file__))
if _THU_MUC_GOC not in sys.path:
    sys.path.insert(0, _THU_MUC_GOC)

from modules.dijkstra_logic import tai_ban_do_osm
from giao_dien.terminal_ui import in_tieu_de, in_thong_bao, in_canh_bao

# Cấu hình
TEN_THANH_PHO = "Vinh, Nghe An, Vietnam"
BAN_KINH_M = 6000
CACHE_FILE = os.path.join(_THU_MUC_GOC, "du_lieu", "cache", "do_thi_osm.pkl")

def main():
    in_tieu_de("PHASE 1: TẢI BẢN ĐỒ ĐƯỜNG PHỐ")

    # Tải bản đồ (chưa cần danh sách điểm — chỉ tải graph thô)
    G, dung_osm = tai_ban_do_osm(TEN_THANH_PHO, BAN_KINH_M, tat_ca_diem=None)

    # Lưu cache (CHỈ graph, chưa có nodes_id)
    os.makedirs(os.path.dirname(CACHE_FILE), exist_ok=True)
    with open(CACHE_FILE, "wb") as f:
        pickle.dump({"graph": G, "dung_osm": dung_osm}, f)

    in_thong_bao(f"✔ Đồ thị: {len(G.nodes):,} nút | {len(G.edges):,} cạnh")
    in_thong_bao(f"✔ Đã lưu cache → {CACHE_FILE}")
    in_canh_bao("Bước tiếp theo: chạy 1b_sinh_khach_hang.py để sinh khách hàng trong vùng này.")

if __name__ == "__main__":
    main()
