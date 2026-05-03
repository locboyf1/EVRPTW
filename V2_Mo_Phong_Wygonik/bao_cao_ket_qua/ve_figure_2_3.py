"""
=============================================================
BAO CAO KET QUA: VE FIGURE (ROUTE MAP + TRADE-OFF + TW)
=============================================================
LUONG DU LIEU:
    ket_qua_tabu.json + khach_hang.json → Route Map
    lich_su_so_sanh.csv                 → Figure 1 (Trade-off)
    lich_su_so_sanh.csv                 → Figure 3 (TW vs Cost/Emit)

OUTPUT:
    du_lieu/figure_route_map.png
    du_lieu/figure_1_tradeoff.png
    du_lieu/figure_3_time_window.png

LUU Y QUAN TRONG (Wygonik & Goodchild 2010):
    - Figure 1 PHAI dung chi so PER ORDER (khong dung tong)
    - Truc X: Emissions (kg CO2 per Order) ← quy doi gram → kg
    - Truc Y: Monetary Cost ($ per Order)
=============================================================
"""

import os
import sys
import json
import pandas as pd
import matplotlib.pyplot as plt

_THU_MUC_SCRIPT = os.path.dirname(os.path.abspath(__file__))
_THU_MUC_GOC = os.path.dirname(_THU_MUC_SCRIPT)

if _THU_MUC_GOC not in sys.path:
    sys.path.insert(0, _THU_MUC_GOC)

from giao_dien.terminal_ui import in_tieu_de, in_thong_bao, in_canh_bao, in_ket_qua

FILE_KET_QUA = os.path.join(_THU_MUC_GOC, "du_lieu", "ket_qua_tabu.json")
FILE_KH      = os.path.join(_THU_MUC_GOC, "du_lieu", "khach_hang.json")
FILE_CSV     = os.path.join(_THU_MUC_GOC, "du_lieu", "lich_su_so_sanh.csv")
THU_MUC_XUAT = os.path.join(_THU_MUC_GOC, "du_lieu")

# Palette mau de phan biet cac xe
MAU_XE = [
    '#e6194b', '#3cb44b', '#4363d8', '#f58231', '#911eb4',
    '#42d4f4', '#f032e6', '#bfef45', '#fabed4', '#469990',
    '#dcbeff', '#9A6324', '#800000', '#aaffc3', '#808000',
    '#000075', '#a9a9a9', '#e6beff', '#ffe119', '#ffd8b1'
]


# ─────────────────────────────────────────────────────────────
# GOM NHOM CSV (dung chung cho Figure 1 va Figure 3)
# ─────────────────────────────────────────────────────────────
def _gom_nhom_csv(df: pd.DataFrame) -> pd.DataFrame:
    """Gom 3 dong (3 ca) thanh 1 kich ban dua tren Lan_Chay."""
    nhom_cols = ["Lan_Chay", "Ten_Kich_Ban", "Che_Do_TW", "Do_Rong_TW"]
    sum_cols = ["So_Khach", "So_Xe_Dung", "Chi_Phi_Tong", "Khi_Thai_Tong"]

    for col in nhom_cols + sum_cols:
        if col not in df.columns:
            in_canh_bao(f"Thieu cot '{col}'!")
            return pd.DataFrame()

    df_gom = df.groupby(nhom_cols, as_index=False)[sum_cols].sum()
    df_gom["Chi_Phi_Per_Order"] = (df_gom["Chi_Phi_Tong"] / df_gom["So_Khach"]).round(4)
    df_gom["Khi_Thai_Per_Order"] = (df_gom["Khi_Thai_Tong"] / df_gom["So_Khach"]).round(4)
    return df_gom


# ═══════════════════════════════════════════════════════════
# ROUTE MAP — BAN DO LO TRINH
# ═══════════════════════════════════════════════════════════
def ve_route_map():
    """
    Ve ban do lo trinh cua tat ca xe.

    HO TRO 2 FORMAT JSON:
        - sw=3: {"PreDawn": {...}, "Breakfast": {...}, "Lunch/Dinner": {...}}
        - sw=1: {"All_Merged": {...}}

    Moi ca duoc ve tren 1 subplot rieng.
    """
    if not os.path.exists(FILE_KET_QUA) or not os.path.exists(FILE_KH):
        in_canh_bao("Thieu file de ve Route Map. Hay chay Tabu Search truoc!")
        return

    # ── Load du lieu ──
    with open(FILE_KET_QUA, "r", encoding="utf-8") as f:
        ket_qua = json.load(f)
    with open(FILE_KH, "r", encoding="utf-8") as f:
        kh_json = json.load(f)

    kho = kh_json["kho_xuat_phat"]
    khach_hang = kh_json["danh_sach_khach_hang"]

    danh_sach_ca = list(ket_qua.keys())
    so_ca = len(danh_sach_ca)
    in_thong_bao(f"Route Map: {so_ca} ca — {danh_sach_ca}")

    # ── Tao figure voi subplots ──
    if so_ca == 1:
        fig, axes = plt.subplots(1, 1, figsize=(10, 9))
        axes = [axes]
    else:
        fig, axes = plt.subplots(1, so_ca, figsize=(7 * so_ca, 8))

    for idx_ca, ten_ca in enumerate(danh_sach_ca):
        ax = axes[idx_ca]
        kq_ca = ket_qua[ten_ca]
        lo_trinh_dict = kq_ca.get("lo_trinh", {})

        # ── Ve kho (ngoi sao do) ──
        ax.scatter(
            kho["kinh_do"], kho["vi_do"],
            marker='*', c='red', s=300, zorder=10,
            edgecolors='black', linewidths=0.8, label='Depot'
        )

        # ── Ve tat ca KH mau xanh nhat ──
        kh_kinh_do = [kh["kinh_do"] for kh in khach_hang]
        kh_vi_do = [kh["vi_do"] for kh in khach_hang]
        ax.scatter(
            kh_kinh_do, kh_vi_do,
            marker='o', c='lightblue', s=30, zorder=3,
            alpha=0.4, edgecolors='gray', linewidths=0.3
        )

        # ── Ve tung xe ──
        dem_xe = 0
        for ten_xe, info_xe in lo_trinh_dict.items():
            thu_tu = info_xe["thu_tu"]
            if not thu_tu:
                continue

            mau = MAU_XE[dem_xe % len(MAU_XE)]
            dem_xe += 1

            # Toa do: Kho → KH1 → KH2 → ... → Kho
            kinh_do_list = [kho["kinh_do"]]
            vi_do_list = [kho["vi_do"]]

            for kh_idx in thu_tu:
                kh = khach_hang[kh_idx]
                kinh_do_list.append(kh["kinh_do"])
                vi_do_list.append(kh["vi_do"])

            kinh_do_list.append(kho["kinh_do"])
            vi_do_list.append(kho["vi_do"])

            ax.plot(kinh_do_list, vi_do_list,
                    '-o', color=mau, markersize=5,
                    linewidth=1.5, alpha=0.8,
                    label=f"{ten_xe} ({len(thu_tu)} KH)")

        # ── Trang tri ──
        so_kh = kq_ca.get("so_khach_hang_trong_tap", "?")
        so_xe_dung = kq_ca.get("so_xe_dung", dem_xe)
        ax.set_title(f"{ten_ca} — {so_kh} KH, {so_xe_dung} xe",
                     fontsize=12, fontweight='bold')
        ax.set_xlabel("Kinh do", fontsize=10)
        ax.set_ylabel("Vi do", fontsize=10)
        ax.grid(True, linestyle='--', alpha=0.4)
        ax.legend(fontsize=7, loc='upper left', ncol=2,
                  framealpha=0.8, borderpad=0.5)

    fig.suptitle("Route Map — Lo Trinh Giao Hang",
                 fontsize=14, fontweight='bold', y=1.01)
    plt.tight_layout()

    fig_path = os.path.join(THU_MUC_XUAT, "figure_route_map.png")
    plt.savefig(fig_path, dpi=150, bbox_inches='tight')
    in_ket_qua(f"Da luu Route Map → {fig_path}")
    plt.close()


# ═══════════════════════════════════════════════════════════
# FIGURE 1: TRADE-OFF CURVE (COST vs EMISSIONS — PER ORDER)
# ═══════════════════════════════════════════════════════════
def ve_figure_1():
    """
    Ve bieu do Trade-off Curve theo chuan Wygonik & Goodchild (2010).

    Truc X: Emissions (kg CO2 PER ORDER) ← chia 1000 tu gram
    Truc Y: Monetary Cost ($ PER ORDER)

    Doc CSV, gom nhom (groupby Lan_Chay), roi ve scatter.
    """
    if not os.path.exists(FILE_CSV):
        in_canh_bao(f"Khong tim thay: {FILE_CSV}")
        return

    df = pd.read_csv(FILE_CSV)
    in_thong_bao(f"Figure 1: Da load {len(df)} dong CSV")

    df_gom = _gom_nhom_csv(df)
    if df_gom.empty:
        in_canh_bao("Khong the gom nhom du lieu cho Figure 1!")
        return

    in_thong_bao(f"  Sau gom nhom: {len(df_gom)} kich ban")

    # ── Du lieu truc ──
    x_data = df_gom["Khi_Thai_Per_Order"] / 1000.0   # gram → kg CO2
    y_data = df_gom["Chi_Phi_Per_Order"]              # $ per order

    # ── Ve bieu do ──
    fig, ax = plt.subplots(figsize=(9, 7))

    ax.scatter(x_data, y_data, c='darkgreen', s=120, zorder=5, edgecolors='black')

    # Annotate tung diem
    for i, row in df_gom.iterrows():
        label = f"{row['Ten_Kich_Ban']} ({row['Che_Do_TW']}, {int(row['Do_Rong_TW'])}p)"
        ax.annotate(
            label,
            (x_data.iloc[i] if isinstance(x_data, pd.Series) else x_data[i],
             y_data.iloc[i] if isinstance(y_data, pd.Series) else y_data[i]),
            xytext=(8, 6), textcoords='offset points',
            fontsize=9, fontstyle='italic'
        )

    ax.set_title("Figure 1: Trade-off Curve (Cost vs Emissions per Order)",
                 fontsize=13, fontweight='bold', pad=15)
    ax.set_xlabel("Emissions (kg CO₂ per Order)", fontsize=11)
    ax.set_ylabel("Monetary Cost ($ per Order)", fontsize=11)
    ax.grid(True, linestyle='--', alpha=0.6)
    ax.text(0.05, 0.95, "Lower-Left is Better",
            transform=ax.transAxes, verticalalignment='top',
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5),
            fontsize=10)

    plt.tight_layout()

    fig1_path = os.path.join(THU_MUC_XUAT, "figure_1_tradeoff.png")
    plt.savefig(fig1_path, dpi=150)
    in_ket_qua(f"Da luu Figure 1 → {fig1_path}")
    plt.close()


# ═══════════════════════════════════════════════════════════
# FIGURE 3: TIME WINDOW vs COST / EMISSIONS
# ═══════════════════════════════════════════════════════════
def ve_figure_3():
    """
    Ve bieu do anh huong cua Do_Rong_TW len Chi phi va Khi thai.

    2 subplots:
        - Trai: Do_Rong_TW (X) vs Chi_Phi_Per_Order (Y)
        - Phai: Do_Rong_TW (X) vs Khi_Thai_Per_Order (Y)

    Moi Ten_Kich_Ban la mot duong rieng (hoac nhom diem).
    """
    if not os.path.exists(FILE_CSV):
        in_canh_bao(f"Khong tim thay: {FILE_CSV}")
        return

    df = pd.read_csv(FILE_CSV)
    in_thong_bao(f"Figure 3: Da load {len(df)} dong CSV")

    df_gom = _gom_nhom_csv(df)
    if df_gom.empty:
        in_canh_bao("Khong the gom nhom du lieu cho Figure 3!")
        return

    # ── Ve 2 subplots ──
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

    # Nhom theo Ten_Kich_Ban de ve tung duong
    for name, group in df_gom.groupby("Ten_Kich_Ban"):
        group_sorted = group.sort_values("Do_Rong_TW")
        x = group_sorted["Do_Rong_TW"]

        # Subplot 1: Cost
        y_cost = group_sorted["Chi_Phi_Per_Order"]
        ax1.plot(x, y_cost, '-o', label=name, markersize=8, linewidth=2)

        # Subplot 2: Emissions
        y_emit = group_sorted["Khi_Thai_Per_Order"]
        ax2.plot(x, y_emit, '-s', label=name, markersize=8, linewidth=2)

    # Trang tri subplot 1
    ax1.set_title("Cost per Order vs Time Window Width",
                  fontsize=12, fontweight='bold')
    ax1.set_xlabel("Time Window Width (minutes)", fontsize=11)
    ax1.set_ylabel("Cost per Order ($)", fontsize=11)
    ax1.grid(True, linestyle='--', alpha=0.6)
    ax1.legend(fontsize=9)

    # Trang tri subplot 2
    ax2.set_title("Emissions per Order vs Time Window Width",
                  fontsize=12, fontweight='bold')
    ax2.set_xlabel("Time Window Width (minutes)", fontsize=11)
    ax2.set_ylabel("Emissions per Order (g CO₂)", fontsize=11)
    ax2.grid(True, linestyle='--', alpha=0.6)
    ax2.legend(fontsize=9)

    fig.suptitle("Figure 3: Impact of Time Window Width on Cost & Emissions",
                 fontsize=14, fontweight='bold', y=1.02)
    plt.tight_layout()

    fig3_path = os.path.join(THU_MUC_XUAT, "figure_3_time_window.png")
    plt.savefig(fig3_path, dpi=150, bbox_inches='tight')
    in_ket_qua(f"Da luu Figure 3 → {fig3_path}")
    plt.close()


# ─────────────────────────────────────────────────────────────
# DIEM KHOI CHAY
# ─────────────────────────────────────────────────────────────
def main():
    in_tieu_de("BAO CAO: VE DO THI (ROUTE MAP + FIGURE 1 + FIGURE 3)")

    ve_route_map()
    ve_figure_1()
    ve_figure_3()

    in_ket_qua("Hoan thanh ve tat ca do thi!")


if __name__ == "__main__":
    main()
