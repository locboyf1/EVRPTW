"""
=============================================================
GIAO DIEN TERMINAL — BAN DOC LAP CHO V2_Mo_Phong_Wygonik
Muc dich: In mau, in tieu de, in tien trinh.
Hoan toan tu chua (self-contained), khong phu thuoc code cu.
=============================================================
"""

import sys


# ─────────────────────────────────────────────────────────────
# BANG MAU ANSI
# ─────────────────────────────────────────────────────────────
class Mau:
    RESET       = "\033[0m"
    XANH_NHAT   = "\033[94m"   # Bright Blue — tieu de
    XANH_DUONG  = "\033[34m"   # Standard Blue — thong bao
    XANH_LUC    = "\033[92m"   # Bright Green — ket qua tot
    VANG        = "\033[93m"   # Yellow — canh bao
    DO          = "\033[91m"   # Red — loi
    TRANG       = "\033[97m"   # Bright White
    XAM         = "\033[90m"   # Gray
    DAM         = "\033[1m"    # Bold


# ─────────────────────────────────────────────────────────────
# CAC HAM IN
# ─────────────────────────────────────────────────────────────
def in_tieu_de(noi_dung: str):
    """In tieu de lon voi khung ke."""
    chieu_rong = 60
    duong_ke = "═" * chieu_rong
    print(f"\n{Mau.XANH_NHAT}{Mau.DAM}{duong_ke}{Mau.RESET}")
    print(f"{Mau.XANH_NHAT}{Mau.DAM}  {noi_dung.center(chieu_rong - 2)}{Mau.RESET}")
    print(f"{Mau.XANH_NHAT}{Mau.DAM}{duong_ke}{Mau.RESET}")


def in_thong_bao(noi_dung: str):
    """In thong bao thuong mau xanh."""
    print(f"{Mau.XANH_DUONG}  {noi_dung}{Mau.RESET}")


def in_canh_bao(noi_dung: str):
    """In canh bao mau vang."""
    print(f"{Mau.VANG}  ⚠ {noi_dung}{Mau.RESET}")


def in_loi(noi_dung: str):
    """In loi mau do."""
    print(f"{Mau.DO}  ✗ LOI: {noi_dung}{Mau.RESET}")


def in_ket_qua(noi_dung: str):
    """In ket qua quan trong mau xanh luc."""
    print(f"{Mau.XANH_LUC}{Mau.DAM}  {noi_dung}{Mau.RESET}")


def in_tien_trinh(phan_tram: float, mo_ta: str = ""):
    """In thanh tien trinh truc quan."""
    chieu_dai_thanh = 30
    so_o_day = int(phan_tram / 100 * chieu_dai_thanh)
    thanh = "█" * so_o_day + "░" * (chieu_dai_thanh - so_o_day)
    sys.stdout.write(
        f"\r{Mau.XANH_NHAT}  [{thanh}] {phan_tram:5.1f}%  {mo_ta}{Mau.RESET}"
    )
    sys.stdout.flush()
    if phan_tram >= 100:
        print()  # Xuong dong khi hoan thanh


def in_duong_ngang():
    """In duong ke ngang phan chia."""
    print(f"{Mau.XAM}  {'─' * 56}{Mau.RESET}")


def in_banner():
    """In banner khoi dong he thong V2."""
    print(f"""
{Mau.XANH_NHAT}{Mau.DAM}
  ╔══════════════════════════════════════════════════════╗
  ║   V2 Mo Phong Wygonik — Modular & Plug-and-Play    ║
  ║   Kien truc: Dijkstra → [.npz] → Tabu Search       ║
  ║   Phien ban: 2.0 | Self-contained                  ║
  ╚══════════════════════════════════════════════════════╝
{Mau.RESET}""")
