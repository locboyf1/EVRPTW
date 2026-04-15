"""
=============================================================
MAIN.PY — ĐIỂM KHỞI ĐỘNG HỆ THỐNG
Điều phối 3 lớp theo đúng thứ tự kiến trúc ArcGIS:

  LỚP 1 → LỚP 2 (Dijkstra) → [Nhân hệ số xe] → LỚP 3 (Tabu)

LUỒNG DỮ LIỆU:
  JSON Files
    └→ [Lớp 1] Tiền xử lý → dict Python
         └→ [Lớp 2] Dijkstra → 4 Ma trận OD gốc
              └→ [Ngoài Dijkstra] Nhân hệ số xe → Ma trận khí thải theo xe
                   └→ [Lớp 3] Tabu Search → Lộ trình tối ưu
                        └→ ket_qua_vrp.json
=============================================================
"""

import sys
import os
import json

# ── Thêm thư mục gốc vào sys.path để import các module ──
_THU_MUC_GOC = os.path.dirname(os.path.abspath(__file__))
if _THU_MUC_GOC not in sys.path:
    sys.path.insert(0, _THU_MUC_GOC)

import numpy as np

# ── Import 3 lớp ──
from lop_1_tien_xu_ly.tao_du_lieu import tai_va_xu_ly_du_lieu
from lop_2_network_analyst.dijkstra_ma_tran_od import (
    tai_do_thi_duong_pho,
    snap_diem_vao_do_thi,
    tao_ma_tran_od_bang_dijkstra,
    ap_dung_he_so_loai_xe          # Hàm nhân hệ số — gọi SAU Dijkstra
)
from lop_3_vrp_solver.tabu_search_vrp import TabuSearchVRPSolver
from giao_dien.terminal_ui import (
    in_banner, in_tieu_de, in_thong_bao, in_ket_qua, in_canh_bao
)


# ─────────────────────────────────────────────────────────────
# CẤU HÌNH CHẠY HỆ THỐNG
# ─────────────────────────────────────────────────────────────
# Đường dẫn tuyệt đối: luôn tính từ vị trí của main.py, không phụ thuộc CWD
CAU_HINH_CHAY = {
    "thu_muc_du_lieu":   os.path.join(_THU_MUC_GOC, "du_lieu"),
    "ten_thanh_pho_osm": "Ho Chi Minh City, Vietnam",
    "ban_kinh_ban_do_m": 8000,      # Bán kính tải bản đồ (mét)
    "ma_xe_giai":        "XE_01",   # Xe được chọn để tính hệ số khí thải
    "tham_so_tabu": {
        "toi_da_vong_lap": 300,
        "do_dai_tabu":     12,
        "trong_so_chi_phi":  0.5,   # α — trọng số chi phí tài chính
        "trong_so_khi_thai": 0.5    # β — trọng số khí thải môi trường
    },
    "luu_ket_qua_json":  True,
    "file_ket_qua":      os.path.join(_THU_MUC_GOC, "ket_qua_vrp.json")
}


# ─────────────────────────────────────────────────────────────
# HÀM CHÍNH
# ─────────────────────────────────────────────────────────────
def chay_he_thong():
    """
    Hàm điều phối trung tâm — chạy 3 lớp theo đúng thứ tự kiến trúc.
    """
    in_banner()

    # ══════════════════════════════════════════════════════════
    # BƯỚC 1: LỚP 1 — TIỀN XỬ LÝ DỮ LIỆU
    # ══════════════════════════════════════════════════════════
    du_lieu = tai_va_xu_ly_du_lieu(CAU_HINH_CHAY["thu_muc_du_lieu"])

    bang_moves   = du_lieu["bang_moves"]
    tat_ca_diem  = du_lieu["tat_ca_diem"]   # index 0 = kho, 1..N = KH
    danh_sach_kh = du_lieu["khach_hang"]    # index 0-based, không chứa kho
    danh_sach_xe = du_lieu["cau_hinh_xe"]
    luong_tai_xe = du_lieu["luong_tai_xe"]

    # Tìm cấu hình xe được chọn
    ma_xe_chon = CAU_HINH_CHAY["ma_xe_giai"]
    cau_hinh_xe_chon = next(
        (xe for xe in danh_sach_xe if xe["ma_xe"] == ma_xe_chon),
        danh_sach_xe[0]
    )
    he_so_khi_thai_xe = cau_hinh_xe_chon["he_so_khi_thai"]

    in_thong_bao(
        f"Xe được chọn: {ma_xe_chon} "
        f"({cau_hinh_xe_chon['loai_xe']}) | "
        f"Hệ số khí thải: ×{he_so_khi_thai_xe} | "
        f"Lương tài xế: ${luong_tai_xe}/giờ (độc lập với hệ số xe)"
    )

    # ══════════════════════════════════════════════════════════
    # BƯỚC 2: LỚP 2 — NETWORK ANALYST (DIJKSTRA)
    # ══════════════════════════════════════════════════════════

    # 2.1: Tải đồ thị đường phố (OSMnx hoặc Euclidean dự phòng)
    do_thi, dung_osmnx = tai_do_thi_duong_pho(
        ten_thanh_pho=CAU_HINH_CHAY["ten_thanh_pho_osm"],
        ban_kinh_met=CAU_HINH_CHAY["ban_kinh_ban_do_m"],
        tat_ca_diem=tat_ca_diem  # Cần khi dùng đồ thị dự phòng
    )

    # 2.2: Snap các điểm vào đồ thị
    danh_sach_node_osm = snap_diem_vao_do_thi(
        do_thi, tat_ca_diem, dung_osmnx
    )

    # 2.3: Chạy Dijkstra → 4 ma trận gốc
    # ⚠ Hàm này chạy XONG TOÀN BỘ trước khi return
    (ma_tran_chi_phi,
     ma_tran_khi_thai_goc,       # Chưa nhân hệ số xe
     ma_tran_thoi_gian_giay,
     ma_tran_quang_duong_km) = tao_ma_tran_od_bang_dijkstra(
        do_thi=do_thi,
        danh_sach_node_osm=danh_sach_node_osm,
        cau_hinh_xe=cau_hinh_xe_chon,
        luong_tai_xe_usd_per_gio=luong_tai_xe,
        bang_moves=bang_moves
    )

    # ══════════════════════════════════════════════════════════
    # BƯỚC 2.4: NHÂN HỆ SỐ LOẠI XE — SAU KHI DIJKSTRA XONG
    # ⚠ ĐIỂM MẤU CHỐT: Bước này nằm NGOÀI và SAU vòng lặp Dijkstra
    #   Nhân bằng numpy broadcasting (1 phép tính duy nhất)
    # ══════════════════════════════════════════════════════════
    in_tieu_de("ÁP DỤNG HỆ SỐ LOẠI XE (SAU DIJKSTRA)")
    ma_tran_khi_thai_xe = ap_dung_he_so_loai_xe(
        ma_tran_khi_thai_goc=ma_tran_khi_thai_goc,
        he_so_khi_thai_xe=he_so_khi_thai_xe
    )

    # ══════════════════════════════════════════════════════════
    # BƯỚC 3: LỚP 3 — VRP SOLVER (TABU SEARCH)
    # Tabu Search nhận 2 ma trận OD đã hoàn thiện
    # → Không biết gì về đồ thị, không gọi Dijkstra
    # ══════════════════════════════════════════════════════════
    tham_so = CAU_HINH_CHAY["tham_so_tabu"]

    bo_giai = TabuSearchVRPSolver(
        so_xe=len(danh_sach_xe),
        danh_sach_khach_hang=danh_sach_kh,
        cau_hinh_xe=danh_sach_xe,
        ma_tran_chi_phi=ma_tran_chi_phi,
        ma_tran_khi_thai=ma_tran_khi_thai_xe,      # ← Ma trận đã nhân hệ số xe
        ma_tran_thoi_gian_giay=ma_tran_thoi_gian_giay,
        toi_da_vong_lap=tham_so["toi_da_vong_lap"],
        do_dai_tabu=tham_so["do_dai_tabu"],
        trong_so_chi_phi=tham_so["trong_so_chi_phi"],
        trong_so_khi_thai=tham_so["trong_so_khi_thai"]
    )

    ket_qua = bo_giai.giai()

    # ══════════════════════════════════════════════════════════
    # BƯỚC 4: LƯU KẾT QUẢ RA FILE JSON
    # ══════════════════════════════════════════════════════════
    if CAU_HINH_CHAY["luu_ket_qua_json"]:
        file_ket_qua = CAU_HINH_CHAY["file_ket_qua"]

        def _chuyen_doi_json(obj):
            """Chuyển numpy types sang Python types để JSON serialize."""
            if isinstance(obj, (np.floating, float)):
                return float(obj)
            if isinstance(obj, (np.integer, int)):
                return int(obj)
            if isinstance(obj, np.ndarray):
                return obj.tolist()
            return obj

        ket_qua_luu = {
            "ham_muc_tieu":  _chuyen_doi_json(ket_qua["ham_muc_tieu"]),
            "tong_chi_phi":  _chuyen_doi_json(ket_qua["tong_chi_phi"]),
            "tong_khi_thai": _chuyen_doi_json(ket_qua["tong_khi_thai"]),
            "lo_trinh": {
                ten_xe: {
                    k: _chuyen_doi_json(v)
                    for k, v in info.items()
                }
                for ten_xe, info in ket_qua["lo_trinh"].items()
            }
        }

        with open(file_ket_qua, "w", encoding="utf-8") as f:
            json.dump(ket_qua_luu, f, ensure_ascii=False, indent=2)
        in_ket_qua(f"\n✔ Kết quả đã lưu: {file_ket_qua}")

    in_tieu_de("HỆ THỐNG HOÀN THÀNH")


# ─────────────────────────────────────────────────────────────
# ĐIỂM KHỞI CHẠY
# ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    chay_he_thong()
