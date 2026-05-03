"""
=============================================================
PHASE 1b: SINH KHÁCH HÀNG NGẪU NHIÊN TRONG VÙNG BẢN ĐỒ
Nhiệm vụ: Đọc đồ thị đã tải (bước 1), lấy bounding box thực tế,
           sinh N khách hàng ngẫu nhiên NẰM TRONG vùng có đường đi.
Input:     du_lieu/cache/do_thi_osm.pkl
Output:    du_lieu/khach_hang.json
=============================================================
"""

import os
import sys
import json
import pickle
import random
import math

# Xác định thư mục gốc dựa trên vị trí file này
_THU_MUC_GOC = os.path.dirname(os.path.abspath(__file__))
if _THU_MUC_GOC not in sys.path:
    sys.path.insert(0, _THU_MUC_GOC)

from giao_dien.terminal_ui import in_tieu_de, in_thong_bao, in_canh_bao, in_ket_qua

# ─────────────────────────────────────────────────────────────
# CẤU HÌNH — BẠN CÓ THỂ CHỈNH SỬA Ở ĐÂY
# ─────────────────────────────────────────────────────────────
CAU_HINH = {
    # Thông tin Kho trung tâm (điểm xuất phát cố định)
    "kho_ten":       "Kho trung tam Vinh",
    "kho_vi_do":     18.7358406,
    "kho_kinh_do":   105.6906101,

    # Số lượng khách hàng cần sinh
    "so_khach_hang": 50,

    # Nhu cầu hàng hóa (đơn vị)
    "nhu_cau_min":   2,
    "nhu_cau_max":   15,

    # Time Window (phút) — mô phỏng ngày làm việc
    "gio_bat_dau":   0,       # Phút bắt đầu
    "gio_ket_thuc":  360,     # Phút kết thúc (6 giờ = 360 phút)
    "do_rong_cua_so": 30,     # Mỗi khách có cửa sổ 30 phút

    # Thời gian bốc dỡ cố định (phút)
    "thoi_gian_boc_do": 10,
}

# Đường dẫn
CACHE_FILE = os.path.join(_THU_MUC_GOC, "du_lieu", "cache", "do_thi_osm.pkl")
OUTPUT_FILE = os.path.join(_THU_MUC_GOC, "du_lieu", "khach_hang.json")


# ─────────────────────────────────────────────────────────────
# HÀM: LẤY BOUNDING BOX TỪ ĐỒ THỊ
# ─────────────────────────────────────────────────────────────
def _lay_bounding_box(G):
    """
    Lấy hình chữ nhật bao quanh (bounding box) của đồ thị.

    Ví dụ trực quan:
    ┌─────────────────────┐ ← (max_lat, max_lon)
    │   ·  ·    ·         │
    │  ·    ·  ·   ·      │  ← Các node đường phố
    │    ·   ·    ·       │
    └─────────────────────┘ ← (min_lat, min_lon)

    Trả về: (min_lat, max_lat, min_lon, max_lon)
    """
    vi_do_list = []
    kinh_do_list = []
    for node_id, data in G.nodes(data=True):
        # OSMnx dùng 'y' cho vĩ độ, 'x' cho kinh độ
        vi_do_list.append(data.get('y', data.get('vi_do', 0)))
        kinh_do_list.append(data.get('x', data.get('kinh_do', 0)))

    return min(vi_do_list), max(vi_do_list), min(kinh_do_list), max(kinh_do_list)


# ─────────────────────────────────────────────────────────────
# HÀM: SINH TỌA ĐỘ NGẪU NHIÊN TRONG BOUNDING BOX
# ─────────────────────────────────────────────────────────────
def _sinh_toa_do_trong_vung(min_lat, max_lat, min_lon, max_lon):
    """
    Sinh một điểm ngẫu nhiên nằm trong hình chữ nhật bounding box.
    Điểm này chắc chắn nằm trong vùng bản đồ đã tải.
    """
    vi_do = random.uniform(min_lat, max_lat)
    kinh_do = random.uniform(min_lon, max_lon)
    return vi_do, kinh_do


# ─────────────────────────────────────────────────────────────
# HÀM CHÍNH: SINH DANH SÁCH KHÁCH HÀNG
# ─────────────────────────────────────────────────────────────
def sinh_khach_hang(G, cau_hinh: dict) -> dict:
    """
    Sinh N khách hàng ngẫu nhiên NẰM TRONG vùng bản đồ đã tải.

    Quy trình:
    1. Lấy bounding box từ đồ thị thực tế
    2. Sinh tọa độ ngẫu nhiên trong bounding box
    3. Gán nhu cầu và time window ngẫu nhiên
    """
    so_kh = cau_hinh["so_khach_hang"]

    # Lấy bounding box từ graph thực tế
    min_lat, max_lat, min_lon, max_lon = _lay_bounding_box(G)

    # Thu hẹp 10% ở mỗi cạnh để tránh sinh điểm ở biên rìa
    # (biên rìa thường ít đường phố, snap node sẽ xa)
    lat_margin = (max_lat - min_lat) * 0.10
    lon_margin = (max_lon - min_lon) * 0.10
    min_lat += lat_margin
    max_lat -= lat_margin
    min_lon += lon_margin
    max_lon -= lon_margin

    # Kho xuất phát (cố định)
    kho = {
        "ten": cau_hinh["kho_ten"],
        "vi_do": cau_hinh["kho_vi_do"],
        "kinh_do": cau_hinh["kho_kinh_do"],
        "thoi_gian_mo_cua": 0,
        "thoi_gian_dong_cua": 1440,
        "thoi_gian_boc_do": 0
    }

    # Sinh từng khách hàng
    danh_sach = []
    for i in range(1, so_kh + 1):
        vi_do, kinh_do = _sinh_toa_do_trong_vung(min_lat, max_lat, min_lon, max_lon)

        nhu_cau = random.randint(cau_hinh["nhu_cau_min"], cau_hinh["nhu_cau_max"])

        mo_cua_max = cau_hinh["gio_ket_thuc"] - cau_hinh["do_rong_cua_so"]
        mo_cua = random.randint(cau_hinh["gio_bat_dau"], max(0, mo_cua_max))
        dong_cua = mo_cua + cau_hinh["do_rong_cua_so"]

        khach_hang = {
            "ten": f"Khach hang {i:02d}",
            "vi_do": round(vi_do, 12),
            "kinh_do": round(kinh_do, 12),
            "nhu_cau": nhu_cau,
            "thoi_gian_mo_cua": mo_cua,
            "thoi_gian_dong_cua": dong_cua,
            "thoi_gian_boc_do": cau_hinh["thoi_gian_boc_do"]
        }
        danh_sach.append(khach_hang)

    return {
        "kho_xuat_phat": kho,
        "danh_sach_khach_hang": danh_sach
    }


# ─────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────
def main():
    in_tieu_de("PHASE 1b: SINH KHÁCH HÀNG TRONG VÙNG BẢN ĐỒ")

    # 1. Đọc graph đã tải từ bước 1
    if not os.path.exists(CACHE_FILE):
        in_canh_bao(f"Không tìm thấy {CACHE_FILE}")
        in_canh_bao("Hãy chạy bước 1 (1_tai_ban_do.py) trước!")
        return

    with open(CACHE_FILE, "rb") as f:
        data = pickle.load(f)
    G = data["graph"]

    # 2. Lấy bounding box để hiển thị
    min_lat, max_lat, min_lon, max_lon = _lay_bounding_box(G)
    in_thong_bao(f"  Vùng bản đồ: vĩ độ [{min_lat:.4f} → {max_lat:.4f}]")
    in_thong_bao(f"               kinh độ [{min_lon:.4f} → {max_lon:.4f}]")
    in_thong_bao(f"  Số node đường phố: {len(G.nodes):,}")

    # 3. In cấu hình
    in_thong_bao(f"  Số khách hàng:     {CAU_HINH['so_khach_hang']}")
    in_thong_bao(f"  Nhu cầu:           {CAU_HINH['nhu_cau_min']} – {CAU_HINH['nhu_cau_max']} đơn vị")
    in_thong_bao(f"  Time Window:       {CAU_HINH['do_rong_cua_so']} phút")

    # 4. Sinh dữ liệu
    du_lieu = sinh_khach_hang(G, CAU_HINH)

    # 5. Lưu file
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(du_lieu, f, ensure_ascii=False, indent=2)

    # 6. Thống kê
    ds = du_lieu["danh_sach_khach_hang"]
    tong_nhu_cau = sum(kh["nhu_cau"] for kh in ds)

    print()
    in_ket_qua(f"✔ Đã sinh {len(ds)} khách hàng trong vùng bản đồ!")
    in_thong_bao(f"  Tổng nhu cầu: {tong_nhu_cau} đơn vị ({tong_nhu_cau/len(ds):.1f}/KH)")
    in_thong_bao(f"  Output: {OUTPUT_FILE}")
    in_canh_bao("⚠ File khach_hang.json cũ đã bị GHI ĐÈ!")
    in_canh_bao("⚠ Chạy tiếp bước 2 → 3 → 4.")


if __name__ == "__main__":
    main()
