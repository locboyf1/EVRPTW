"""
=============================================================
DU LIEU IO: XUAT MA TRAN OD RA FILE CSV (Human-readable)
=============================================================
LUONG DU LIEU:
    Ma_Tran_OD.npz  (do MAY tao ra tu Dijkstra)
    khach_hang.json  (ten khach hang de lam header)
         │
         ▼
    [SCRIPT NAY]
         │
         ▼
    Ma_Tran_Chi_Phi.csv
    Ma_Tran_Thoi_Gian.csv
    Ma_Tran_Khi_Thai.csv
    Ma_Tran_Quang_Duong.csv

MUC DICH:
    - Mo bang Excel de kiem tra so lieu
    - In nop bao cao khoa hoc
    - Header hang/cot = TEN KHACH HANG (lay tu khach_hang.json)
=============================================================
"""

import os
import sys
import json
import numpy as np

# ─────────────────────────────────────────────────────────────
# XAC DINH THU MUC GOC
# ─────────────────────────────────────────────────────────────
_THU_MUC_SCRIPT = os.path.dirname(os.path.abspath(__file__))
_THU_MUC_GOC = os.path.dirname(_THU_MUC_SCRIPT)

if _THU_MUC_GOC not in sys.path:
    sys.path.insert(0, _THU_MUC_GOC)

from giao_dien.terminal_ui import in_tieu_de, in_thong_bao, in_canh_bao, in_ket_qua, in_loi


# ─────────────────────────────────────────────────────────────
# DUONG DAN FILE
# ─────────────────────────────────────────────────────────────
FILE_MA_TRAN_NPZ = os.path.join(_THU_MUC_GOC, "du_lieu", "Ma_Tran_OD.npz")
FILE_KHACH_HANG  = os.path.join(_THU_MUC_GOC, "du_lieu", "khach_hang.json")
THU_MUC_XUAT     = os.path.join(_THU_MUC_GOC, "du_lieu")  # Xuat CSV cung thu muc du_lieu


# ─────────────────────────────────────────────────────────────
# HAM: LAY DANH SACH TEN DIEM (Kho + Khach hang)
# ─────────────────────────────────────────────────────────────
def _lay_danh_sach_ten(file_kh: str) -> list:
    """
    Doc khach_hang.json va tra ve danh sach ten theo dung thu tu
    index trong ma tran OD.

    Vi du output:
        ["Kho trung tam Vinh", "Khach hang 01", "Khach hang 02", ...]
         index 0 (kho)         index 1          index 2

    Cac ten nay se duoc gan vao header Cot va Hang cua file CSV.
    """
    with open(file_kh, "r", encoding="utf-8") as f:
        data = json.load(f)

    kho = data["kho_xuat_phat"]
    khach_hang = data["danh_sach_khach_hang"]

    danh_sach_ten = [kho["ten"]]
    for kh in khach_hang:
        danh_sach_ten.append(kh["ten"])

    return danh_sach_ten


# ─────────────────────────────────────────────────────────────
# HAM: XUAT 1 MA TRAN RA FILE CSV
# ─────────────────────────────────────────────────────────────
def _xuat_mot_ma_tran_csv(ma_tran: np.ndarray,
                           danh_sach_ten: list,
                           duong_dan_csv: str,
                           don_vi: str = "",
                           so_thap_phan: int = 4):
    """
    Xuat 1 ma tran numpy N×N ra file CSV voi header la ten khach hang.

    Vi du file CSV output (mo bang Excel):
    ┌──────────────────┬──────────────┬──────────────┬─────────────┐
    │                  │ Kho TT Vinh  │ Khach hang 01│ Khach hang 02│
    ├──────────────────┼──────────────┼──────────────┼─────────────┤
    │ Kho TT Vinh      │    0.0000    │    2.3456    │    1.7890   │
    │ Khach hang 01    │    2.3456    │    0.0000    │    3.1234   │
    │ Khach hang 02    │    1.7890    │    3.1234    │    0.0000   │
    └──────────────────┴──────────────┴──────────────┴─────────────┘

    Tham so:
        ma_tran:       numpy array N×N
        danh_sach_ten: list[str] do rong N
        duong_dan_csv: duong dan file .csv output
        don_vi:        mo ta don vi (chi de in thong bao)
        so_thap_phan:  so chu so thap phan
    """
    n = ma_tran.shape[0]

    with open(duong_dan_csv, "w", encoding="utf-8-sig") as f:
        # ── Dong header (hang dau tien) ──
        # Cot dau trong (goc trai tren), sau do la ten cac diem
        header = [""] + danh_sach_ten
        f.write(",".join(header) + "\n")

        # ── Cac dong du lieu ──
        for i in range(n):
            ten_hang = danh_sach_ten[i]
            cac_gia_tri = []
            for j in range(n):
                gia_tri = ma_tran[i][j]
                if gia_tri == float("inf") or np.isinf(gia_tri):
                    cac_gia_tri.append("INF")
                else:
                    cac_gia_tri.append(f"{gia_tri:.{so_thap_phan}f}")

            dong = [ten_hang] + cac_gia_tri
            f.write(",".join(dong) + "\n")

    in_thong_bao(f"  ✔ {os.path.basename(duong_dan_csv):30s} ({don_vi}) → {n}×{n}")


# ─────────────────────────────────────────────────────────────
# HAM CHINH: XUAT TAT CA MA TRAN RA CSV
# ─────────────────────────────────────────────────────────────
def xuat_tat_ca_csv():
    """
    Doc Ma_Tran_OD.npz va xuat ra 4 file CSV tuong ung.

    Mapping ten key trong .npz → ten file CSV:
        cp → Ma_Tran_Chi_Phi.csv      (USD)
        tg → Ma_Tran_Thoi_Gian.csv    (giay)
        kt → Ma_Tran_Khi_Thai.csv     (gram CO2)
        km → Ma_Tran_Quang_Duong.csv  (km)
    """
    in_tieu_de("XUAT MA TRAN OD RA CSV (Human-readable)")

    # ── Kiem tra file ton tai ──
    if not os.path.exists(FILE_MA_TRAN_NPZ):
        in_loi(f"Khong tim thay file: {FILE_MA_TRAN_NPZ}")
        in_canh_bao("Hay chay Dijkstra truoc de tao Ma_Tran_OD.npz!")
        return

    if not os.path.exists(FILE_KHACH_HANG):
        in_loi(f"Khong tim thay file: {FILE_KHACH_HANG}")
        in_canh_bao("Hay chay sinh khach hang truoc!")
        return

    # ── Load du lieu ──
    matrices = np.load(FILE_MA_TRAN_NPZ)
    danh_sach_ten = _lay_danh_sach_ten(FILE_KHACH_HANG)

    in_thong_bao(f"Da load Ma_Tran_OD.npz: {len(matrices.files)} ma tran")
    in_thong_bao(f"Da load {len(danh_sach_ten)} ten diem (kho + khach hang)")
    in_thong_bao(f"Dang xuat CSV vao: {THU_MUC_XUAT}")
    print()

    # ── Xuat tung ma tran ──
    # Moi cap: (key trong npz, ten file csv, don vi, so thap phan)
    danh_sach_xuat = [
        ("cp", "Ma_Tran_Chi_Phi.csv",      "USD",      4),
        ("tg", "Ma_Tran_Thoi_Gian.csv",    "giay",     2),
        ("kt", "Ma_Tran_Khi_Thai.csv",     "gram CO2", 4),
        ("km", "Ma_Tran_Quang_Duong.csv",  "km",       4),
    ]

    so_xuat = 0
    for key, ten_file, don_vi, thap_phan in danh_sach_xuat:
        if key in matrices:
            duong_dan = os.path.join(THU_MUC_XUAT, ten_file)
            _xuat_mot_ma_tran_csv(
                ma_tran=matrices[key],
                danh_sach_ten=danh_sach_ten,
                duong_dan_csv=duong_dan,
                don_vi=don_vi,
                so_thap_phan=thap_phan
            )
            so_xuat += 1
        else:
            in_canh_bao(f"  Key '{key}' khong ton tai trong .npz — bo qua")

    print()
    in_ket_qua(f"Hoan thanh! Da xuat {so_xuat} file CSV.")
    in_thong_bao("Mo bang Excel de kiem tra so lieu va nop bao cao.")


# ─────────────────────────────────────────────────────────────
# DIEM KHOI CHAY
# ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    xuat_tat_ca_csv()
