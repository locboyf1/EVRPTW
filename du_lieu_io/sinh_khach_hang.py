"""
=============================================================
DU LIEU IO: SINH KHACH HANG NGAU NHIEN TRONG VUNG BAN DO
=============================================================
LUONG DU LIEU:
    cau_hinh_co_so.json
         │
         ▼
    do_thi_osm.pkl (graph da tai tu buoc 1)
         │
         ▼
    [SCRIPT NAY] → khach_hang.json

DIEM MOI SO VOI BAN CU (sinh_khach_hang.py):
    - Doc CAU HINH tu file JSON tap trung (khong hardcode)
    - HO TRO 3 CA HOAT DONG: PreDawn / Breakfast / Lunch-Dinner
    - HO TRO CHE DO "All" (Scenario 1): gop 3 ca theo ty le bai bao
    - TIME WINDOW xuat ra dang chuoi "HH:MM" de doc
    - RE NHANH logic Time Window:
        + "mixed"  → Random do rong theo ty le phan phoi cua bai bao
        + "fixed"  → Ep do rong = do_rong_cua_so_phut cho tat ca
    - thoi_gian_boc_do lay tu cau hinh (khong hardcode)
=============================================================
"""

import os
import sys
import json
import pickle
import random
import math
import networkx as nx

# ─────────────────────────────────────────────────────────────
# XAC DINH THU MUC GOC (V2_Mo_Phong_Wygonik/)
# ─────────────────────────────────────────────────────────────
_THU_MUC_SCRIPT = os.path.dirname(os.path.abspath(__file__))
_THU_MUC_GOC = os.path.dirname(_THU_MUC_SCRIPT)

if _THU_MUC_GOC not in sys.path:
    sys.path.insert(0, _THU_MUC_GOC)

from giao_dien.terminal_ui import in_tieu_de, in_thong_bao, in_canh_bao, in_ket_qua, in_loi


# ─────────────────────────────────────────────────────────────
# DUONG DAN FILE
# ─────────────────────────────────────────────────────────────
FILE_CAU_HINH    = os.path.join(_THU_MUC_GOC, "cau_hinh", "cau_hinh_co_so.json")
FILE_DO_THI_CACHE = os.path.join(_THU_MUC_GOC, "du_lieu", "do_thi_osm.pkl")
FILE_KHACH_HANG  = os.path.join(_THU_MUC_GOC, "du_lieu", "khach_hang.json")


# ─────────────────────────────────────────────────────────────
# HAM PHU TRO: CHUYEN DOI THOI GIAN HH:MM <-> PHUT
# ─────────────────────────────────────────────────────────────
def time_to_minutes(hh_mm_str: str) -> int:
    """
    Chuyen chuoi "HH:MM" thanh so phut (int).

    Vi du:
        "07:00" → 420
        "13:00" → 780
        "02:30" → 150
    """
    h, m = hh_mm_str.split(":")
    return int(h) * 60 + int(m)


def minutes_to_time(minutes_int: int) -> str:
    """
    Chuyen so phut (int) thanh chuoi "HH:MM".

    Vi du:
        420 → "07:00"
        780 → "13:00"
        150 → "02:30"
    """
    h = minutes_int // 60
    m = minutes_int % 60
    return f"{h:02d}:{m:02d}"


# ─────────────────────────────────────────────────────────────
# HAM: DOC CAU HINH TU JSON
# ─────────────────────────────────────────────────────────────
def doc_cau_hinh() -> dict:
    """
    Doc file cau_hinh_co_so.json va tra ve dict.

    Vi du noi dung file:
    {
        "so_khach_hang": 50,
        "che_do_time_window": "mixed",
        "do_rong_cua_so_phut": 60,
        "thoi_gian_boc_do_phut": 10,
        "ca_hoat_dong_hien_tai": "Breakfast",
        "danh_sach_ca_hoat_dong": { ... },
        "kho_xuat_phat": {"ten": "Kho trung tam Vinh", ...}
    }
    """
    if not os.path.exists(FILE_CAU_HINH):
        in_loi(f"Khong tim thay file cau hinh: {FILE_CAU_HINH}")
        raise FileNotFoundError(FILE_CAU_HINH)

    with open(FILE_CAU_HINH, "r", encoding="utf-8") as f:
        return json.load(f)


# ─────────────────────────────────────────────────────────────
# HAM: LAY BOUNDING BOX TU DO THI
# ─────────────────────────────────────────────────────────────
def _lay_bounding_box(G) -> tuple:
    """
    Lay hinh chu nhat bao quanh (bounding box) cua do thi.

    Vi du truc quan:
    ┌─────────────────────┐ ← (max_lat, max_lon)
    │   ·  ·    ·         │
    │  ·    ·  ·   ·      │  ← Cac node duong pho
    │    ·   ·    ·       │
    └─────────────────────┘ ← (min_lat, min_lon)

    Tra ve: (min_lat, max_lat, min_lon, max_lon)
    """
    vi_do_list = []
    kinh_do_list = []
    for _, data in G.nodes(data=True):
        vi_do_list.append(data.get('y', data.get('vi_do', 0)))
        kinh_do_list.append(data.get('x', data.get('kinh_do', 0)))

    return min(vi_do_list), max(vi_do_list), min(kinh_do_list), max(kinh_do_list)


# ─────────────────────────────────────────────────────────────
# HAM: SINH TOA DO NGAU NHIEN TRONG VUNG
# ─────────────────────────────────────────────────────────────
def _sinh_toa_do_trong_vung(min_lat, max_lat, min_lon, max_lon) -> tuple:
    """Sinh 1 diem ngau nhien nam trong bounding box."""
    vi_do = random.uniform(min_lat, max_lat)
    kinh_do = random.uniform(min_lon, max_lon)
    return round(vi_do, 12), round(kinh_do, 12)


# ─────────────────────────────────────────────────────────────
# HAM: SINH TIME WINDOW (THEO CA HOAT DONG + TY LE BAI BAO)
# ─────────────────────────────────────────────────────────────
def _sinh_time_window(che_do: str, do_rong_co_dinh: int,
                      gio_bat_dau_phut: int, gio_ket_thuc_phut: int,
                      ten_ca: str) -> tuple:
    """
    Sinh (thoi_gian_mo_cua, thoi_gian_dong_cua) cho 1 khach hang.
    Don vi tra ve: PHUT TUYET DOI (vd: 420 = 07:00).

    LOGIC THEO CA:
    ┌────────────────────────────────────────────────────────┐
    │ PreDawn:                                               │
    │   → Khoa cung: mo_cua = bat_dau, dong_cua = ket_thuc  │
    │   → Moi KH deu co cua so = chieu dai ca               │
    ├────────────────────────────────────────────────────────┤
    │ Breakfast (mixed):                                     │
    │   → ~33% KH co do rong 180 phut (3 tieng)             │
    │   → ~67% KH co do rong 60 phut (1 tieng)              │
    ├────────────────────────────────────────────────────────┤
    │ Lunch/Dinner (mixed):                                  │
    │   → ~60% KH co do rong 180 phut (3 tieng)             │
    │   → ~20% KH co do rong 120 phut (2 tieng)             │
    │   → ~20% KH co do rong 60 phut (1 tieng)              │
    ├────────────────────────────────────────────────────────┤
    │ fixed (moi ca):                                        │
    │   → Ep do rong = do_rong_co_dinh cho tat ca KH        │
    └────────────────────────────────────────────────────────┘
    """
    chieu_dai_ca = gio_ket_thuc_phut - gio_bat_dau_phut

    # ── PreDawn: KHOA CUNG ──
    if ten_ca == "PreDawn":
        return gio_bat_dau_phut, gio_ket_thuc_phut

    # ── XAC DINH DO RONG CUA SO ──
    if che_do == "mixed":
        if ten_ca == "Breakfast":
            do_rong = 180 if random.random() < (1.0 / 3.0) else 60
        elif ten_ca == "Lunch/Dinner":
            r = random.random()
            if r < 0.60:
                do_rong = 180
            elif r < 0.80:
                do_rong = 120
            else:
                do_rong = 60
        else:
            do_rong = random.choice([60, 120, 180])
    elif che_do == "fixed":
        do_rong = do_rong_co_dinh
    else:
        do_rong = do_rong_co_dinh

    # Dam bao do rong khong vuot chieu dai ca
    do_rong = min(do_rong, chieu_dai_ca)

    # ── SINH THOI GIAN MO CUA NGAU NHIEN (nam gon trong ca) ──
    mo_cua_max = gio_ket_thuc_phut - do_rong
    mo_cua = random.randint(gio_bat_dau_phut, mo_cua_max)
    dong_cua = mo_cua + do_rong

    return mo_cua, dong_cua


# ─────────────────────────────────────────────────────────────
# TY LE CHIA KHACH HANG KHI GOP CA (SCENARIO 1 — BAI BAO)
# ─────────────────────────────────────────────────────────────
# Du lieu goc tu bai bao Wygonik & Goodchild (2010):
#   PreDawn:      283 / 576 ≈ 49.13%
#   Breakfast:    140 / 576 ≈ 24.31%
#   Lunch/Dinner: 153 / 576 ≈ 26.56%
# ─────────────────────────────────────────────────────────────
TY_LE_GOP_CA = {
    "PreDawn":      283 / 576,   # ~49.13%
    "Breakfast":    140 / 576,   # ~24.31%
    "Lunch/Dinner": 153 / 576,   # ~26.56%
}


def _chia_so_khach_theo_ty_le(tong_so_kh: int) -> dict:
    """
    Chia tong_so_kh thanh 3 nhom ty le thuan voi bai bao.

    Vi du voi tong_so_kh = 100:
        PreDawn:      49
        Breakfast:    24
        Lunch/Dinner: 27  (phan du gom vao nhom cuoi)

    Tra ve: dict {"PreDawn": 49, "Breakfast": 24, "Lunch/Dinner": 27}
    """
    ket_qua = {}
    da_phan = 0

    ten_ca_list = list(TY_LE_GOP_CA.keys())

    for i, ten_ca in enumerate(ten_ca_list):
        if i < len(ten_ca_list) - 1:
            # Lam tron xuong cho cac nhom dau
            so_kh = math.floor(tong_so_kh * TY_LE_GOP_CA[ten_ca])
            ket_qua[ten_ca] = so_kh
            da_phan += so_kh
        else:
            # Nhom cuoi: lay phan con lai de dam bao tong = tong_so_kh
            ket_qua[ten_ca] = tong_so_kh - da_phan

    return ket_qua


# ─────────────────────────────────────────────────────────────
# HAM SINH TOA DO + SNAP (dung chung cho ca 2 che do)
# ─────────────────────────────────────────────────────────────
def _sinh_1_khach_hang_toa_do(G, ox, min_lat, max_lat, min_lon, max_lon,
                               thanh_phan_lon_nhat, so_lan_thu_toi_da=100):
    """
    Sinh toa do ngau nhien, snap vao node lien thong.
    Tra ve: (vi_do, kinh_do, da_tim_duoc, so_lan_bi_loai_them)
    """
    so_lan_bi_loai = 0
    da_tim_duoc = False
    vi_do, kinh_do = 0.0, 0.0

    for _ in range(so_lan_thu_toi_da):
        vi_do, kinh_do = _sinh_toa_do_trong_vung(
            min_lat, max_lat, min_lon, max_lon
        )
        node_snap = ox.distance.nearest_nodes(G, X=kinh_do, Y=vi_do)
        if node_snap in thanh_phan_lon_nhat:
            da_tim_duoc = True
            break
        else:
            so_lan_bi_loai += 1

    return vi_do, kinh_do, da_tim_duoc, so_lan_bi_loai


# ─────────────────────────────────────────────────────────────
# HAM CHINH: SINH DANH SACH KHACH HANG
# ─────────────────────────────────────────────────────────────
def sinh_khach_hang(G, cau_hinh: dict) -> dict:
    """
    Sinh N khach hang ngau nhien TRONG vung ban do da tai.

    HO TRO 2 CHE DO:
    ┌────────────────────────────────────────────────────────┐
    │ ca_hoat_dong_hien_tai == "All" (Scenario 1):           │
    │   → Chia so_khach_hang theo ty le bai bao              │
    │   → Sinh 3 vong lap (PreDawn, Breakfast, Lunch/Dinner) │
    │   → Gop tat ca vao 1 danh sach chung                   │
    ├────────────────────────────────────────────────────────┤
    │ ca_hoat_dong_hien_tai == "Breakfast" / khac:           │
    │   → Sinh toan bo so_khach_hang bang luat cua ca do     │
    └────────────────────────────────────────────────────────┘

    Tra ve:
        dict co cau truc giong khach_hang.json
    """
    import osmnx as ox

    so_kh = cau_hinh["so_khach_hang"]
    che_do_tw = cau_hinh["che_do_time_window"]
    do_rong_cd = cau_hinh["do_rong_cua_so_phut"]
    thoi_gian_boc_do = cau_hinh["thoi_gian_boc_do_phut"]
    ds_ca = cau_hinh["danh_sach_ca_hoat_dong"]

    # ── Lay bounding box va thu hep 10% ──
    min_lat, max_lat, min_lon, max_lon = _lay_bounding_box(G)
    lat_margin = (max_lat - min_lat) * 0.10
    lon_margin = (max_lon - min_lon) * 0.10
    min_lat += lat_margin
    max_lat -= lat_margin
    min_lon += lon_margin
    max_lon -= lon_margin

    in_thong_bao(f"Vung sinh KH: vi do [{min_lat:.4f} → {max_lat:.4f}]")
    in_thong_bao(f"              kinh do [{min_lon:.4f} → {max_lon:.4f}]")
    in_thong_bao(f"Che do Time Window: {che_do_tw}")
    in_thong_bao(f"Thoi gian boc do: {thoi_gian_boc_do} phut (tu cau hinh)")

    # ── Tim thanh phan lien thong lon nhat ──
    thanh_phan_lon_nhat = max(
        nx.strongly_connected_components(G), key=len
    )
    in_thong_bao(
        f"Thanh phan lien thong lon nhat: {len(thanh_phan_lon_nhat):,} / "
        f"{len(G.nodes):,} node ({len(thanh_phan_lon_nhat)/len(G.nodes)*100:.1f}%)"
    )

    # ── Kho xuat phat ──
    kho_cfg = cau_hinh["kho_xuat_phat"]
    kho = {
        "ten": kho_cfg["ten"],
        "vi_do": kho_cfg["vi_do"],
        "kinh_do": kho_cfg["kinh_do"],
        "thoi_gian_mo_cua": "00:00",
        "thoi_gian_dong_cua": "23:59",
        "thoi_gian_boc_do": 0,
        "nhu_cau": 0
    }

    # ══════════════════════════════════════════════════════════
    # LUON SINH CHO CA 3 CA THEO TY LE BAI BAO
    # ══════════════════════════════════════════════════════════
    phan_bo = _chia_so_khach_theo_ty_le(so_kh)
    danh_sach_viec = list(phan_bo.items())  # [(ten_ca, so_kh_ca), ...]

    in_thong_bao(f"Sinh {so_kh} KH cho 3 ca:")
    for ten_ca, so_kh_ca in danh_sach_viec:
        ca_cfg = ds_ca[ten_ca]
        in_thong_bao(f"  {ten_ca}: {so_kh_ca} KH ({ca_cfg['bat_dau']} → {ca_cfg['ket_thuc']})")

    # ══════════════════════════════════════════════════════════
    # VONG LAP SINH KHACH HANG (CHUNG CHO CA 2 CHE DO)
    # ══════════════════════════════════════════════════════════
    SO_LAN_THU_TOI_DA = 100
    danh_sach = []
    so_lan_bi_loai = 0
    dem_kh = 0  # Bo dem lien tuc de danh so KH

    for ten_ca, so_kh_ca in danh_sach_viec:
        ca_cfg = ds_ca[ten_ca]
        gio_bat_dau = time_to_minutes(ca_cfg["bat_dau"])
        gio_ket_thuc = time_to_minutes(ca_cfg["ket_thuc"])

        for i in range(so_kh_ca):
            dem_kh += 1

            vi_do, kinh_do, da_tim, loai_them = _sinh_1_khach_hang_toa_do(
                G, ox, min_lat, max_lat, min_lon, max_lon,
                thanh_phan_lon_nhat, SO_LAN_THU_TOI_DA
            )
            so_lan_bi_loai += loai_them

            if not da_tim:
                in_canh_bao(f"  KH {dem_kh:02d}: Thu {SO_LAN_THU_TOI_DA} lan van bi co lap! Dung diem cuoi.")

            nhu_cau = random.randint(2, 15)

            # Sinh time window (PHUT TUYET DOI)
            mo_cua_phut, dong_cua_phut = _sinh_time_window(
                che_do_tw, do_rong_cd,
                gio_bat_dau, gio_ket_thuc,
                ten_ca
            )

            # XUAT DANG CHUOI "HH:MM" + GAN NHAN CA
            khach_hang = {
                "ten": f"Khach hang {dem_kh:02d}",
                "vi_do": vi_do,
                "kinh_do": kinh_do,
                "nhu_cau": nhu_cau,
                "thoi_gian_mo_cua": minutes_to_time(mo_cua_phut),
                "thoi_gian_dong_cua": minutes_to_time(dong_cua_phut),
                "thoi_gian_boc_do": thoi_gian_boc_do,
                "ca_hoat_dong": ten_ca
            }
            danh_sach.append(khach_hang)

    if so_lan_bi_loai > 0:
        in_canh_bao(f"Da loai {so_lan_bi_loai} toa do bi co lap (sinh lai thanh cong).")
    else:
        in_ket_qua("Tat ca KH deu nam tren thanh phan lien thong chinh!")

    return {
        "kho_xuat_phat": kho,
        "danh_sach_khach_hang": danh_sach
    }


# ─────────────────────────────────────────────────────────────
# DIEM KHOI CHAY (chay doc lap)
# ─────────────────────────────────────────────────────────────
def main():
    in_tieu_de("DU LIEU IO: SINH KHACH HANG TRONG VUNG BAN DO")

    # 1. Doc cau hinh
    cau_hinh = doc_cau_hinh()

    in_thong_bao(f"So khach hang can sinh: {cau_hinh['so_khach_hang']}")
    phan_bo = _chia_so_khach_theo_ty_le(cau_hinh['so_khach_hang'])
    for ca, sl in phan_bo.items():
        in_thong_bao(f"  {ca}: {sl} KH")
    in_thong_bao(f"Che do Time Window:     {cau_hinh['che_do_time_window']}")
    in_thong_bao(f"Do rong cua so (fixed): {cau_hinh['do_rong_cua_so_phut']} phut")
    in_thong_bao(f"Thoi gian boc do:       {cau_hinh['thoi_gian_boc_do_phut']} phut")

    # 2. Doc do thi tu cache
    if not os.path.exists(FILE_DO_THI_CACHE):
        in_canh_bao(f"Khong tim thay {FILE_DO_THI_CACHE}")
        in_canh_bao("Hay chay buoc tai ban do truoc (thuat_toan_dijkstra.py phan tai)!")
        return

    with open(FILE_DO_THI_CACHE, "rb") as f:
        data = pickle.load(f)
    G = data["graph"]
    in_thong_bao(f"Da load do thi: {len(G.nodes):,} nut")

    # 3. Sinh du lieu
    du_lieu = sinh_khach_hang(G, cau_hinh)

    # 4. Luu file
    os.makedirs(os.path.dirname(FILE_KHACH_HANG), exist_ok=True)
    with open(FILE_KHACH_HANG, "w", encoding="utf-8") as f:
        json.dump(du_lieu, f, ensure_ascii=False, indent=2)

    # 5. Thong ke
    ds = du_lieu["danh_sach_khach_hang"]
    tong_nhu_cau = sum(kh["nhu_cau"] for kh in ds)

    # Thong ke do rong cua so (chuyen HH:MM → phut de tinh)
    do_rong_list = [
        time_to_minutes(kh["thoi_gian_dong_cua"]) - time_to_minutes(kh["thoi_gian_mo_cua"])
        for kh in ds
    ]
    do_rong_min = min(do_rong_list)
    do_rong_max = max(do_rong_list)
    do_rong_tb = sum(do_rong_list) / len(do_rong_list)

    print()
    in_ket_qua(f"Da sinh {len(ds)} khach hang!")
    in_thong_bao(f"  Tong nhu cau:   {tong_nhu_cau} don vi ({tong_nhu_cau/len(ds):.1f}/KH)")
    in_thong_bao(f"  Do rong cua so: min={do_rong_min}, max={do_rong_max}, TB={do_rong_tb:.1f} phut")
    in_thong_bao(f"  Vi du KH dau tien: mo={ds[0]['thoi_gian_mo_cua']}, dong={ds[0]['thoi_gian_dong_cua']}")
    in_thong_bao(f"  Output: {FILE_KHACH_HANG}")
    in_canh_bao("File khach_hang.json cu da bi GHI DE!")


if __name__ == "__main__":
    main()
