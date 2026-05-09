"""
=============================================================
LOI GIAI MANG LUOI: DIJKSTRA — TAO MA TRAN OD (FULL CODE)
=============================================================
LUONG DU LIEU:
    do_thi_osm.pkl  (graph da tai tu buoc 1_tai_ban_do.py)
    khach_hang.json  (danh sach KH da sinh tu 1b_sinh_khach_hang.py)
    cau_hinh_co_so.json (danh_sach_xe -> profile xe)
         |
         v
    [SCRIPT NAY]
         |
         v
    Ma_Tran_OD.npz  (4 ma tran: cp, kt, tg, km)
         |
         v
    (loi_giai_lo_trinh/ se TU LOAD file nay — khong goi ham cheo)

NGUYEN TAC:
    - Chi phi = hao_mon_xe ($/km) + luong_tai_xe ($/gio * gio)
    - Khi thai goc = TONG (chieu_dai_canh_km * he_so_MOVES_cua_canh)
      (Phuong phap vi phan chieu dai — tinh tung canh rieng)
    - SAU vong lap: khi_thai_final = khi_thai_goc * ty_le_phat_thai_xe
    - Ket qua luu vao .npz de loi_giai_lo_trinh/ load doc lap
=============================================================
"""

import os
import sys
import json
import pickle
import numpy as np
import networkx as nx

_THU_MUC_SCRIPT = os.path.dirname(os.path.abspath(__file__))
_THU_MUC_GOC = os.path.dirname(_THU_MUC_SCRIPT)

if _THU_MUC_GOC not in sys.path:
    sys.path.insert(0, _THU_MUC_GOC)

from giao_dien.terminal_ui import (
    in_tieu_de, in_thong_bao, in_canh_bao, in_ket_qua, in_loi, in_tien_trinh
)

# ─────────────────────────────────────────────────────────────
# DUONG DAN FILE
# ─────────────────────────────────────────────────────────────
FILE_CAU_HINH     = os.path.join(_THU_MUC_GOC, "cau_hinh", "cau_hinh_co_so.json")
FILE_DO_THI_CACHE = os.path.join(_THU_MUC_GOC, "du_lieu", "do_thi_osm.pkl")
FILE_KHACH_HANG   = os.path.join(_THU_MUC_GOC, "du_lieu", "khach_hang.json")
FILE_OUTPUT_NPZ   = os.path.join(_THU_MUC_GOC, "du_lieu", "Ma_Tran_OD.npz")

# Hang so mac dinh
TOC_DO_MAC_DINH_KM_H = 50
HE_SO_KHI_THAI_MAC_DINH = 0.261   # g/km — tra bang MOVES khi khong co du lieu
CHI_PHI_HAO_MON_USD_PER_KM = 0.15  # USD/km — hao mon xe

# Bang MOVES (Motor Vehicle Emission Simulator)
# Mapping: toc do gioi han (km/h) → he so xa thai CO2 (g/km)
BANG_MOVES = {
    20: 0.312, 30: 0.285, 40: 0.261, 50: 0.248,
    60: 0.239, 70: 0.244, 80: 0.258, 90: 0.275,
    100: 0.298, 110: 0.324, 120: 0.356
}


# ─────────────────────────────────────────────────────────────
# HAM: SNAP DIEM VAO NODE GAN NHAT
# ─────────────────────────────────────────────────────────────
def snap_diem_vao_do_thi(G, tat_ca_diem: list) -> list:
    """
    Tim node OSM gan nhat cho moi diem (kho + KH).

    Su dung ox.distance.nearest_nodes de tim node gan nhat
    tren do thi cho moi toa do (vi_do, kinh_do).

    Tham so:
        G:           Do thi NetworkX (MultiDiGraph tu OSMnx)
        tat_ca_diem: list[dict] — index 0 = kho, 1..N = KH
                     Moi dict co key: "vi_do", "kinh_do", "ten"

    Tra ve:
        danh_sach_node: list[int] — node_id OSM tuong ung voi tung diem
    """
    import osmnx as ox

    in_thong_bao("Dang snap cac diem vao mang luoi duong pho...")
    danh_sach_node = []

    for i, diem in enumerate(tat_ca_diem):
        node_gan_nhat = ox.distance.nearest_nodes(
            G,
            X=diem["kinh_do"],   # Longitude = X
            Y=diem["vi_do"]      # Latitude  = Y
        )
        danh_sach_node.append(node_gan_nhat)
        ten = diem.get("ten", f"Diem {i}")
        in_thong_bao(f"  [{i:02d}] {ten:25s} -> Node OSM: {node_gan_nhat}")

    in_ket_qua(f"Da snap {len(danh_sach_node)} diem vao do thi")
    return danh_sach_node


# ─────────────────────────────────────────────────────────────
# HAM CHINH: TAO MA TRAN OD BANG DIJKSTRA
# ─────────────────────────────────────────────────────────────
def tao_ma_tran_od(G, danh_sach_node: list,
                   luong_tai_xe_usd_per_gio: float) -> tuple:
    """
    Chay Dijkstra cho tung cap (i,j) → 4 ma tran goc N×N.

    LUONG XU LY:
    ┌─────────────────────────────────────────────────────────┐
    │  For i in range(N):                                     │
    │    Dijkstra tu node_i → tat ca node khac (1 lan)        │
    │    For j in range(N):                                   │
    │      1. Lay duong di shortest path (theo travel_time)   │
    │      2. Voi MOI CANH trong duong di:                    │
    │         a. Lay speed cua canh → lam tron boi 10         │
    │         b. Tra BANG_MOVES → he so xa thai rieng canh    │
    │         c. kt_canh = (length/1000) * he_so_moves       │
    │         d. Cong don vao tong_kt_goc                     │
    │      3. Tinh chi_phi = hao_mon + luong_tai_xe           │
    │  END                                                    │
    └─────────────────────────────────────────────────────────┘

    Tham so:
        G:                Do thi NetworkX (co thuoc tinh travel_time, length, speed_kph)
        danh_sach_node:   list[int] — node_id OSM (index 0 = kho)
        luong_tai_xe_usd_per_gio: float — luong $/gio (vd: 26.55)

    Tra ve:
        (ma_tran_cp, ma_tran_kt_goc, ma_tran_tg, ma_tran_km)
        Tat ca la numpy array N×N.
        ma_tran_kt_goc: CHUA nhan he so loai xe (nhan sau)
    """
    in_tieu_de("DIJKSTRA — XAY DUNG MA TRAN OD")

    so_diem = len(danh_sach_node)

    # Khoi tao 4 ma tran rong N×N
    ma_tran_cp = np.zeros((so_diem, so_diem))  # USD
    ma_tran_kt = np.zeros((so_diem, so_diem))  # gram CO2 (chua nhan hybrid)
    ma_tran_tg = np.zeros((so_diem, so_diem))  # giay
    ma_tran_km = np.zeros((so_diem, so_diem))  # km

    tong_cap = so_diem * so_diem
    dem = 0

    in_thong_bao(f"Dang xu ly {so_diem} x {so_diem} = {tong_cap} cap diem...")
    in_canh_bao("Buoc nay la nut co chai — chay mot lan roi luu cache...")

    # ═══════════════════════════════════════════════════════════
    # TOI UU: Dung single_source_dijkstra cho tung nguon i
    # Thay vi goi shortest_path N×N lan, chi can N lan
    # ═══════════════════════════════════════════════════════════
    for i in range(so_diem):
        node_nguon = danh_sach_node[i]

        # Dijkstra tu node_nguon toi tat ca node khac (theo travel_time)
        try:
            distances, paths = nx.single_source_dijkstra(
                G, source=node_nguon, weight="travel_time"
            )
        except Exception:
            # Fallback: node co lap
            in_canh_bao(f"  Node {node_nguon} (diem {i}) khong ket noi. Gan inf.")
            for j in range(so_diem):
                if i != j:
                    ma_tran_cp[i][j] = float("inf")
                    ma_tran_kt[i][j] = float("inf")
                    ma_tran_tg[i][j] = float("inf")
                    ma_tran_km[i][j] = float("inf")
            dem += so_diem
            continue

        for j in range(so_diem):
            dem += 1
            if i == j:
                continue  # Duong cheo = 0

            node_dich = danh_sach_node[j]

            if node_dich not in paths:
                # Khong tim duoc duong
                ma_tran_cp[i][j] = float("inf")
                ma_tran_kt[i][j] = float("inf")
                ma_tran_tg[i][j] = float("inf")
                ma_tran_km[i][j] = float("inf")
                continue

            duong_di = paths[node_dich]

            # ── Tich luy tung canh: chieu dai, thoi gian, khi thai ──
            tong_dai_m = 0.0
            tong_tg_s = 0.0
            tong_kt_goc = 0.0

            for k in range(len(duong_di) - 1):
                u = duong_di[k]
                v = duong_di[k + 1]
                canh = min(
                    G[u][v].values(),
                    key=lambda c: c.get("travel_time", float("inf"))
                )
                dai_canh_m = canh.get("length", 0)
                tg_canh_s = canh.get("travel_time", 0)
                speed = canh.get("speed_kph", TOC_DO_MAC_DINH_KM_H)

                tong_dai_m += dai_canh_m
                tong_tg_s += tg_canh_s

                # ── Vi phan chieu dai: tra MOVES cho RIENG canh nay ──
                toc_do_tra = max(20, min(120, (int(speed) // 10) * 10))
                he_so_moves = BANG_MOVES.get(toc_do_tra, HE_SO_KHI_THAI_MAC_DINH)
                kt_canh = (dai_canh_m / 1000.0) * he_so_moves
                tong_kt_goc += kt_canh

            # Chuyen doi don vi
            tong_dai_km = tong_dai_m / 1000.0
            tong_tg_gio = tong_tg_s / 3600.0

            # ── Chi phi = hao mon + luong tai xe ──
            cp_hao_mon = tong_dai_km * CHI_PHI_HAO_MON_USD_PER_KM
            cp_luong = tong_tg_gio * luong_tai_xe_usd_per_gio
            tong_cp = cp_hao_mon + cp_luong

            # ── Ghi vao ma tran ──
            ma_tran_cp[i][j] = tong_cp
            ma_tran_kt[i][j] = tong_kt_goc
            ma_tran_tg[i][j] = tong_tg_s
            ma_tran_km[i][j] = tong_dai_km

        # Hien thi tien trinh moi nguon
        phan_tram = (i + 1) / so_diem * 100
        in_tien_trinh(phan_tram, f"Dijkstra: nguon {i+1}/{so_diem}")

    print()  # Xuong dong sau thanh tien trinh
    in_ket_qua("Dijkstra hoan thanh. Ma tran OD goc da san sang.")
    return ma_tran_cp, ma_tran_kt, ma_tran_tg, ma_tran_km


# ─────────────────────────────────────────────────────────────
# DIEM KHOI CHAY DOC LAP
# ─────────────────────────────────────────────────────────────
def main():
    """
    Pipeline Dijkstra doc lap:
    1. Doc cau hinh
    2. Load do thi tu cache (.pkl)
    3. Load khach hang (.json)
    4. Snap diem vao do thi
    5. Chay Dijkstra → 4 ma tran goc
    6. Nhan he so loai xe vao khi thai
    7. Luu Ma_Tran_OD.npz
    """
    in_tieu_de("LOI GIAI MANG LUOI: DIJKSTRA -> MA TRAN OD")

    # ── 1. Doc cau hinh ──
    if not os.path.exists(FILE_CAU_HINH):
        in_loi(f"Khong tim thay: {FILE_CAU_HINH}")
        return
    with open(FILE_CAU_HINH, "r", encoding="utf-8") as f:
        cau_hinh = json.load(f)

    # Lay thong so xe tu profile duoc chon
    loai_xe = cau_hinh["loai_xe_su_dung"]
    profile_xe = cau_hinh["danh_sach_xe"][loai_xe]
    luong_tai_xe = profile_xe["luong"]
    he_so_loai_xe = profile_xe["ty_le_phat_thai"]

    in_thong_bao(f"Loai xe: {loai_xe} | Luong: {luong_tai_xe} | "
                 f"Ty le phat thai: x{he_so_loai_xe}")

    # ── 2. Load do thi tu cache ──
    if not os.path.exists(FILE_DO_THI_CACHE):
        in_loi(f"Khong tim thay: {FILE_DO_THI_CACHE}")
        in_canh_bao("Hay chay 1_tai_ban_do.py truoc!")
        return

    with open(FILE_DO_THI_CACHE, "rb") as f:
        cache_data = pickle.load(f)
    G = cache_data["graph"]
    in_thong_bao(f"Da load do thi: {len(G.nodes):,} nut | {len(G.edges):,} canh")

    # ── 3. Load khach hang ──
    if not os.path.exists(FILE_KHACH_HANG):
        in_loi(f"Khong tim thay: {FILE_KHACH_HANG}")
        in_canh_bao("Hay chay 1b_sinh_khach_hang.py truoc!")
        return

    with open(FILE_KHACH_HANG, "r", encoding="utf-8") as f:
        kh_json = json.load(f)

    kho = kh_json["kho_xuat_phat"]
    khach_hang = kh_json["danh_sach_khach_hang"]
    tat_ca_diem = [kho] + khach_hang
    in_thong_bao(f"Da load {len(khach_hang)} khach hang + 1 kho")

    # ── 4. Snap diem vao do thi ──
    danh_sach_node = snap_diem_vao_do_thi(G, tat_ca_diem)

    # ── 5. Chay Dijkstra → 4 ma tran goc ──
    cp, kt_goc, tg, km = tao_ma_tran_od(G, danh_sach_node, luong_tai_xe)

    # ── 6. Nhan he so loai xe SAU KHI Dijkstra xong ──
    # Day la diem mau chot kien truc: do thi khong biet xe nao dang di
    # Chi sau khi xuat ma tran, moi ap dung dac tinh xe
    kt_final = kt_goc * he_so_loai_xe
    in_thong_bao(f"Da ap dung he so loai xe [{loai_xe}]: x{he_so_loai_xe} "
                 f"(Khi thai thay doi {(he_so_loai_xe - 1) * 100:+.0f}%)")

    # ── 7. Luu Ma_Tran_OD.npz ──
    os.makedirs(os.path.dirname(FILE_OUTPUT_NPZ), exist_ok=True)
    np.savez(FILE_OUTPUT_NPZ, cp=cp, kt=kt_final, tg=tg, km=km)
    in_ket_qua(f"Da luu 4 ma tran OD -> {FILE_OUTPUT_NPZ}")
    in_thong_bao(f"  cp: chi phi USD     ({cp.shape})")
    in_thong_bao(f"  kt: khi thai gram   ({kt_final.shape}) — da nhan {loai_xe}")
    in_thong_bao(f"  tg: thoi gian giay  ({tg.shape})")
    in_thong_bao(f"  km: quang duong km  ({km.shape})")


if __name__ == "__main__":
    main()
