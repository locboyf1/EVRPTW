"""
=============================================================
LỚP 1: TIỀN XỬ LÝ DỮ LIỆU
Nhiệm vụ: Đọc và xác thực các file JSON cấu hình.
          Sinh mảng Python thuần túy để truyền vào Lớp 2 & 3.
=============================================================
"""

import json
import os
import sys

# Thêm đường dẫn gốc vào sys.path để import được các module khác
_THU_MUC_GOC = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _THU_MUC_GOC not in sys.path:
    sys.path.insert(0, _THU_MUC_GOC)

from giao_dien.terminal_ui import in_tieu_de, in_thong_bao, in_canh_bao, in_loi


# ─────────────────────────────────────────────────────────────
# HÀM: ĐỌC FILE JSON AN TOÀN
# ─────────────────────────────────────────────────────────────
def doc_json(duong_dan_file: str) -> dict:
    """Đọc file JSON và trả về dict Python. Báo lỗi rõ ràng nếu không tìm thấy."""
    if not os.path.exists(duong_dan_file):
        in_loi(f"Không tìm thấy file: {duong_dan_file}")
        raise FileNotFoundError(f"File không tồn tại: {duong_dan_file}")
    with open(duong_dan_file, "r", encoding="utf-8") as f:
        du_lieu = json.load(f)
    in_thong_bao(f"✔ Đã đọc: {os.path.basename(duong_dan_file)}")
    return du_lieu


# ─────────────────────────────────────────────────────────────
# HÀM CHÍNH: TẢI VÀ XÁC THỰC TOÀN BỘ DỮ LIỆU
# ─────────────────────────────────────────────────────────────
def tai_va_xu_ly_du_lieu(thu_muc_du_lieu: str = "du_lieu") -> dict:
    """
    Đọc 3 file JSON, xác thực tính hợp lệ và trả về dict tổng hợp.

    Trả về:
        {
            'bang_moves':    dict {toc_do_int: he_so_float},
            'cau_hinh_xe':   list[dict] (danh sách các xe),
            'luong_tai_xe':  float (USD/giờ),
            'kho':           dict (thông tin kho xuất phát),
            'khach_hang':    list[dict] (danh sách KH, không kể kho),
            'tat_ca_diem':   list[dict] (kho + KH, index 0 = kho)
        }
    """
    in_tieu_de("LỚP 1: TIỀN XỬ LÝ DỮ LIỆU")

    # --- Đọc 3 file JSON ---
    du_lieu_khi_thai = doc_json(os.path.join(thu_muc_du_lieu, "du_lieu_khi_thai.json"))
    cau_hinh_xe_json = doc_json(os.path.join(thu_muc_du_lieu, "cau_hinh_xe.json"))
    khach_hang_json  = doc_json(os.path.join(thu_muc_du_lieu, "khach_hang.json"))

    # --- Trích xuất bảng MOVES (chuyển key sang int) ---
    bang_moves = {
        int(k): float(v)
        for k, v in du_lieu_khi_thai["bang_moves"].items()
    }

    # --- Trích xuất cấu hình xe ---
    danh_sach_xe = cau_hinh_xe_json["danh_sach_xe"]
    luong_tai_xe = float(cau_hinh_xe_json["luong_tai_xe_usd_per_gio"])

    # --- Trích xuất danh sách điểm ---
    kho     = khach_hang_json["kho_xuat_phat"]
    diem_kh = khach_hang_json["danh_sach_khach_hang"]

    # Gộp: index 0 = kho, 1..N = khách hàng
    tat_ca_diem = [kho] + diem_kh

    # --- Xác thực ---
    _xac_thuc_du_lieu(tat_ca_diem, danh_sach_xe)

    in_thong_bao(f"✔ Tổng số điểm (kho + khách hàng): {len(tat_ca_diem)}")
    in_thong_bao(f"✔ Số xe trong đội:                  {len(danh_sach_xe)}")
    in_thong_bao(
        f"✔ Mức lương tài xế:                 "
        f"${luong_tai_xe}/giờ (biến độc lập theo thời gian)"
    )

    return {
        "bang_moves":   bang_moves,
        "cau_hinh_xe":  danh_sach_xe,
        "luong_tai_xe": luong_tai_xe,
        "kho":          kho,
        "khach_hang":   diem_kh,
        "tat_ca_diem":  tat_ca_diem,
    }


# ─────────────────────────────────────────────────────────────
# HÀM PHỤ: XÁC THỰC DỮ LIỆU
# ─────────────────────────────────────────────────────────────
def _xac_thuc_du_lieu(tat_ca_diem: list, danh_sach_xe: list):
    """Kiểm tra tính hợp lệ cơ bản của dữ liệu đầu vào."""
    for diem in tat_ca_diem:
        if diem["thoi_gian_mo_cua"] > diem["thoi_gian_dong_cua"]:
            raise ValueError(
                f"[LỖI] Điểm '{diem['ten']}': "
                f"thoi_gian_mo_cua ({diem['thoi_gian_mo_cua']}) "
                f"> thoi_gian_dong_cua ({diem['thoi_gian_dong_cua']})"
            )
    for xe in danh_sach_xe:
        if xe["he_so_khi_thai"] <= 0:
            raise ValueError(
                f"[LỖI] Xe '{xe['ma_xe']}': he_so_khi_thai phải > 0"
            )
    in_thong_bao("✔ Xác thực dữ liệu: Hợp lệ")


# ─────────────────────────────────────────────────────────────
# HÀM: LƯU LỊCH SỬ CHẠY (LOGGING)
# ─────────────────────────────────────────────────────────────
def luu_lich_su_chay(file_csv: str, data: dict):
    """
    Lưu kết quả mô phỏng vào file CSV lịch sử.
    data = {
        'Thanh_Pho': str,
        'So_Khach': int,
        'Alpha': float,
        'Beta': float,
        'Chi_Phi': float,
        'Khi_Thai': float,
        'Kich_Ban': str
    }
    """
    import csv
    from datetime import datetime

    file_exists = os.path.isfile(file_csv)
    header = ["Thoi_Gian", "Thanh_Pho", "So_Khach", "Alpha", "Beta", "Chi_Phi", "Khi_Thai", "Kich_Ban"]

    try:
        with open(file_csv, mode='a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            # Nếu file mới, ghi header trước
            if not file_exists:
                writer.writerow(header)
            
            # Chuẩn bị dòng dữ liệu
            row = [
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                data.get("Thanh_Pho", "Unknown"),
                data.get("So_Khach", 0),
                data.get("Alpha", 0.5),
                data.get("Beta", 0.5),
                round(data.get("Chi_Phi", 0), 2),
                round(data.get("Khi_Thai", 0), 2),
                data.get("Kich_Ban", "Base Case")
            ]
            writer.writerow(row)
        in_thong_bao(f"✔ Đã ghi lịch sử chạy vào: {os.path.basename(file_csv)}")
    except Exception as e:
        in_canh_bao(f"⚠ Không thể ghi lịch sử chạy: {e}")
