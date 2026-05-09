"""
=============================================================
KHOI CHAY: GHEP TOAN BO PIPELINE
=============================================================
LUONG THUC THI:
    1. Doc cau_hinh_co_so.json
    2. [du_lieu_io]         1b_sinh_khach_hang.py  → khach_hang.json
    3. [loi_giai_mang_luoi] thuat_toan_dijkstra.py → Ma_Tran_OD.npz
    4. [du_lieu_io]         2b_xuat_ma_tran_csv.py → .csv (tuy chon)
    5. [loi_giai_lo_trinh]  thuat_toan_tabu.py     → ket_qua_tabu.json
    6. [bao_cao_ket_qua]    in_table_2_3 + ve_figure_2_3

LUU Y:
    - Giua buoc 3 va buoc 5, KHONG co import cheo
    - Dijkstra luu .npz, Tabu Search load .npz
    - Script nay chi DIEU PHOI, khong chua logic nghiep vu
=============================================================
"""

import os
import sys
import subprocess

_THU_MUC_SCRIPT = os.path.dirname(os.path.abspath(__file__))
_THU_MUC_GOC = os.path.dirname(_THU_MUC_SCRIPT)

if _THU_MUC_GOC not in sys.path:
    sys.path.insert(0, _THU_MUC_GOC)

from giao_dien.terminal_ui import in_tieu_de, in_thong_bao, in_canh_bao, in_ket_qua, in_banner


def chay_script(duong_dan: str, mo_ta: str):
    """Chay 1 script Python con va in ket qua."""
    in_thong_bao(f"Dang chay: {mo_ta}...")
    in_thong_bao(f"  File: {duong_dan}")
    ket_qua = subprocess.run(
        [sys.executable, duong_dan],
        cwd=_THU_MUC_GOC,
        capture_output=False
    )
    if ket_qua.returncode != 0:
        in_canh_bao(f"Script {mo_ta} ket thuc voi loi (code {ket_qua.returncode})")
    else:
        in_ket_qua(f"  {mo_ta} — HOAN THANH")
    return ket_qua.returncode


def main():
    in_banner()
    in_tieu_de("KICH BAN GOC — CHAY TOAN BO PIPELINE")

    # TODO: Bo comment tung buoc khi da cai dat xong

    # Buoc 1: Sinh khach hang
    # chay_script(
    #     os.path.join(_THU_MUC_GOC, "du_lieu_io", "1b_sinh_khach_hang.py"),
    #     "Sinh khach hang"
    # )

    # Buoc 2: Dijkstra → Ma Tran OD
    # chay_script(
    #     os.path.join(_THU_MUC_GOC, "loi_giai_mang_luoi", "thuat_toan_dijkstra.py"),
    #     "Dijkstra → Ma Tran OD"
    # )

    # Buoc 3 (tuy chon): Xuat CSV cho nguoi doc
    # chay_script(
    #     os.path.join(_THU_MUC_GOC, "du_lieu_io", "2b_xuat_ma_tran_csv.py"),
    #     "Xuat CSV human-readable"
    # )

    # Buoc 4: Tabu Search
    # chay_script(
    #     os.path.join(_THU_MUC_GOC, "loi_giai_lo_trinh", "thuat_toan_tabu.py"),
    #     "Tabu Search"
    # )

    # Buoc 5: Bao cao
    # chay_script(
    #     os.path.join(_THU_MUC_GOC, "bao_cao_ket_qua", "in_table_2_3.py"),
    #     "In Table 2 & 3"
    # )
    # chay_script(
    #     os.path.join(_THU_MUC_GOC, "bao_cao_ket_qua", "ve_figure_2_3.py"),
    #     "Ve Figure 2 & 3"
    # )

    in_canh_bao("SKELETON — Hay bo comment cac buoc khi da cai dat xong.")
    in_tieu_de("PIPELINE HOAN THANH")


if __name__ == "__main__":
    main()
