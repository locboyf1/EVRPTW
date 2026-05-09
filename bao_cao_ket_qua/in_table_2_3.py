"""
=============================================================
BAO CAO KET QUA: IN TABLE 2 & TABLE 3
=============================================================
LUONG DU LIEU:
    lich_su_so_sanh.csv → [SCRIPT NAY] → In bang ra terminal

TABLE 2: So sanh chi phi giua cac kich ban
TABLE 3: So sanh khi thai + % giam CO2

LOGIC GOM NHOM:
    - Dung Lan_Chay de gom 3 dong (3 ca) thanh 1 kich ban
    - Tinh lai Per Order = Tong / So_Khach sau khi gom
=============================================================
"""

import os
import sys
import pandas as pd

_THU_MUC_SCRIPT = os.path.dirname(os.path.abspath(__file__))
_THU_MUC_GOC = os.path.dirname(_THU_MUC_SCRIPT)

if _THU_MUC_GOC not in sys.path:
    sys.path.insert(0, _THU_MUC_GOC)

from giao_dien.terminal_ui import in_tieu_de, in_thong_bao, in_canh_bao, in_ket_qua

FILE_CSV = os.path.join(_THU_MUC_GOC, "du_lieu", "lich_su_so_sanh.csv")


# ─────────────────────────────────────────────────────────────
# GOM NHOM DU LIEU: 3 ca → 1 kich ban
# ─────────────────────────────────────────────────────────────
def gom_nhom_du_lieu(df: pd.DataFrame) -> pd.DataFrame:
    """
    Gom cac dong cung Lan_Chay lai thanh 1 dong tong.

    Vi du:  3 dong (PreDawn 49KH + Breakfast 24KH + Lunch 27KH)
         → 1 dong (Default, 100KH, tong chi phi, tong khi thai)

    Sau do tinh lai Per Order = Tong / So_Khach.
    """
    nhom_cols = ["Lan_Chay", "Ten_Kich_Ban", "Che_Do_TW", "Do_Rong_TW"]
    sum_cols = ["So_Khach", "So_Xe_Dung", "Chi_Phi_Tong", "Khi_Thai_Tong"]

    # Kiem tra cot ton tai
    for col in nhom_cols + sum_cols:
        if col not in df.columns:
            in_canh_bao(f"Thieu cot '{col}' trong CSV!")
            return pd.DataFrame()

    # Gom nhom va tinh tong
    df_gom = df.groupby(nhom_cols, as_index=False)[sum_cols].sum()

    # Tinh lai Per Order tren du lieu da gom
    df_gom["Chi_Phi_Per_Order"] = (
        df_gom["Chi_Phi_Tong"] / df_gom["So_Khach"]
    ).round(4)
    df_gom["Khi_Thai_Per_Order"] = (
        df_gom["Khi_Thai_Tong"] / df_gom["So_Khach"]
    ).round(4)

    return df_gom


# ─────────────────────────────────────────────────────────────
# TABLE 2: SCENARIO COST COMPARISONS
# ─────────────────────────────────────────────────────────────
def in_table_2(df_gom: pd.DataFrame):
    """
    In Table 2 — So sanh chi phi giua cac kich ban.

    Cot: Ten Kich Ban | So KH | So Xe | Tong Chi Phi | Chi Phi/Order
    """
    in_tieu_de("TABLE 2: SCENARIO COST COMPARISONS")

    if df_gom.empty:
        in_canh_bao("Khong co du lieu de in Table 2!")
        return

    # Chon va dinh dang cot
    t2 = df_gom[["Ten_Kich_Ban", "Che_Do_TW", "Do_Rong_TW",
                  "So_Khach", "So_Xe_Dung",
                  "Chi_Phi_Tong", "Chi_Phi_Per_Order"]].copy()

    t2.columns = ["Kich_Ban", "TW_Mode", "TW_Width",
                   "Orders", "Vehicles",
                   "Total_Cost ($)", "Cost/Order ($)"]

    print()
    print(t2.to_string(index=False))
    print()


# ─────────────────────────────────────────────────────────────
# TABLE 3: SCENARIO EMISSIONS COMPARISONS
# ─────────────────────────────────────────────────────────────
def in_table_3(df_gom: pd.DataFrame):
    """
    In Table 3 — So sanh khi thai + % giam CO2 so voi Baseline.

    Cot: Ten Kich Ban | Tong Khi Thai | Khi Thai/Order | % Giam CO2
    Baseline = dong dau tien (dung de tinh %).
    """
    in_tieu_de("TABLE 3: SCENARIO EMISSIONS COMPARISONS")

    if df_gom.empty:
        in_canh_bao("Khong co du lieu de in Table 3!")
        return

    t3 = df_gom[["Ten_Kich_Ban", "Che_Do_TW", "Do_Rong_TW",
                  "So_Khach", "Khi_Thai_Tong", "Khi_Thai_Per_Order"]].copy()

    # Tinh % giam CO2 so voi dong dau tien (Baseline)
    baseline_kt = t3["Khi_Thai_Tong"].iloc[0]
    if baseline_kt > 0:
        t3["Giam_CO2_%"] = (
            (baseline_kt - t3["Khi_Thai_Tong"]) / baseline_kt * 100
        ).round(2)
    else:
        t3["Giam_CO2_%"] = 0.0

    t3.columns = ["Kich_Ban", "TW_Mode", "TW_Width",
                   "Orders", "Total_Emit (g)", "Emit/Order (g)", "CO2_Reduce_%"]

    print()
    print(t3.to_string(index=False))
    print()

    # Ghi chu
    in_thong_bao(f"Baseline (dong 1): {baseline_kt:.2f}g tong khi thai")
    in_thong_bao("% Giam CO2 = (Baseline - Current) / Baseline × 100")


# ─────────────────────────────────────────────────────────────
# DIEM KHOI CHAY
# ─────────────────────────────────────────────────────────────
def main():
    in_tieu_de("BAO CAO: TABLE 2 & TABLE 3")

    if not os.path.exists(FILE_CSV):
        in_canh_bao(f"Khong tim thay: {FILE_CSV}")
        in_canh_bao("Hay chay Tabu Search truoc!")
        return

    # 1. Doc CSV
    df = pd.read_csv(FILE_CSV)
    in_thong_bao(f"Da load {len(df)} dong tu lich_su_so_sanh.csv")
    in_thong_bao(f"Cac cot: {list(df.columns)}")

    # 2. Gom nhom
    df_gom = gom_nhom_du_lieu(df)
    in_thong_bao(f"Sau gom nhom: {len(df_gom)} kich ban")

    # 3. In Table 2 & Table 3
    in_table_2(df_gom)
    in_table_3(df_gom)

    in_ket_qua("Hoan thanh in Table 2 & Table 3!")


if __name__ == "__main__":
    main()
