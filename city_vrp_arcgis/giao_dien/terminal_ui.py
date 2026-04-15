"""
=============================================================
GIAO DIEN TERMINAL -- MINIMALIST BLUE PASTEL THEME
Thiet ke: Mau xanh duong nhat (ANSI escape codes)
=============================================================
"""

import sys
import io

# Ep stdout dung UTF-8 de tranh loi UnicodeEncodeError tren Windows
if hasattr(sys.stdout, 'buffer'):
    sys.stdout = io.TextIOWrapper(
        sys.stdout.buffer,
        encoding='utf-8',
        errors='replace',
        line_buffering=True
    )


# ─────────────────────────────────────────────────────────────
# BẢN MÀU ANSI — BLUE/LIGHT PASTEL THEME
# ─────────────────────────────────────────────────────────────
class Mau:
    RESET        = "\033[0m"
    # Xanh dương nhạt (pastel)
    XANH_NHAT   = "\033[94m"   # Bright Blue — dùng cho tiêu đề
    XANH_DUONG  = "\033[34m"   # Standard Blue — dùng cho thông báo
    XANH_LUC    = "\033[92m"   # Bright Green — dùng cho kết quả tốt
    VANG        = "\033[93m"   # Yellow — dùng cho cảnh báo
    DO          = "\033[91m"   # Red — dùng cho lỗi
    TRANG_NHAT  = "\033[97m"   # Bright White — dùng cho text chính
    XAM         = "\033[90m"   # Gray — dùng cho phụ
    DAM         = "\033[1m"    # Bold
    GACH_CHAN   = "\033[4m"    # Underline


# ─────────────────────────────────────────────────────────────
# HÀM IN CÁC LOẠI THÔNG BÁO
# ─────────────────────────────────────────────────────────────
def in_tieu_de(noi_dung: str):
    """In tieu de lon theo phong cach ArcGIS-inspired."""
    chieu_rong = 60
    duong_ke   = "=" * chieu_rong
    print(f"\n{Mau.XANH_NHAT}{Mau.DAM}{duong_ke}{Mau.RESET}")
    print(f"{Mau.XANH_NHAT}{Mau.DAM}  {noi_dung.center(chieu_rong - 2)}{Mau.RESET}")
    print(f"{Mau.XANH_NHAT}{Mau.DAM}{duong_ke}{Mau.RESET}")


def in_thong_bao(noi_dung: str):
    """In thông báo thông thường màu xanh nhạt."""
    print(f"{Mau.XANH_DUONG}  {noi_dung}{Mau.RESET}")


def in_canh_bao(noi_dung: str):
    """In cảnh báo màu vàng."""
    print(f"{Mau.VANG}  ⚠ {noi_dung}{Mau.RESET}")


def in_loi(noi_dung: str):
    """In thông báo lỗi màu đỏ."""
    print(f"{Mau.DO}  ✗ LỖI: {noi_dung}{Mau.RESET}")


def in_ket_qua(noi_dung: str):
    """In kết quả quan trọng màu xanh lục."""
    print(f"{Mau.XANH_LUC}{Mau.DAM}  {noi_dung}{Mau.RESET}")


def in_tien_trinh(phan_tram: float, mo_ta: str = ""):
    """In thanh tien trinh truc quan."""
    chieu_dai_thanh = 30
    so_o_day = int(phan_tram / 100 * chieu_dai_thanh)
    thanh = "#" * so_o_day + "." * (chieu_dai_thanh - so_o_day)
    sys.stdout.write(
        f"\r{Mau.XANH_NHAT}  [{thanh}] {phan_tram:5.1f}%  {mo_ta}{Mau.RESET}"
    )
    sys.stdout.flush()
    if phan_tram >= 100:
        print()


def in_duong_ngang():
    """In duong ke ngang phan chia."""
    print(f"{Mau.XAM}  {'-' * 56}{Mau.RESET}")


def in_banner():
    """In banner khoi dong he thong."""
    print(f"""
{Mau.XANH_NHAT}{Mau.DAM}
  +======================================================+
  |     CITY VRP -- ArcGIS Network Analyst Clone        |
  |     Kien truc 3 Lop: Dijkstra --> Tabu Search       |
  |     Phien ban: 1.0 | Ngon ngu: Python + OSMnx       |
  +======================================================+
{Mau.RESET}""")
