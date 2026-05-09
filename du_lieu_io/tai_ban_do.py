"""
=============================================================
DU LIEU IO: TAI BAN DO TU OPENSTREETMAP
=============================================================
LUONG DU LIEU:
    cau_hinh_co_so.json  (ten_thanh_pho, ban_kinh_ban_do_m)
         |
         v
    [SCRIPT NAY]  (osmnx download + add speeds/travel_times)
         |
         v
    du_lieu/do_thi_osm.pkl  (pickle cache)

LUU Y:
    - Buoc nay mat 1-3 phut lan dau (tai tu OSM server)
    - Cac lan sau chi can load lai cache, khong tai lai
    - File nay KHONG import bat ky module nao tu V1 cu
=============================================================
"""

import os
import sys
import json
import pickle

_THU_MUC_SCRIPT = os.path.dirname(os.path.abspath(__file__))
_THU_MUC_GOC = os.path.dirname(_THU_MUC_SCRIPT)

if _THU_MUC_GOC not in sys.path:
    sys.path.insert(0, _THU_MUC_GOC)

from giao_dien.terminal_ui import (
    in_tieu_de, in_thong_bao, in_canh_bao, in_ket_qua, in_loi
)

# ─────────────────────────────────────────────────────────────
# DUONG DAN FILE
# ─────────────────────────────────────────────────────────────
FILE_CAU_HINH = os.path.join(_THU_MUC_GOC, "cau_hinh", "cau_hinh_co_so.json")
FILE_CACHE    = os.path.join(_THU_MUC_GOC, "du_lieu", "do_thi_osm.pkl")


# ─────────────────────────────────────────────────────────────
# HAM CHINH: TAI BAN DO
# ─────────────────────────────────────────────────────────────
def tai_ban_do_osm(ten_thanh_pho: str, ban_kinh_m: int):
    """
    Tai do thi duong pho tu OpenStreetMap qua thu vien osmnx.

    Quy trinh:
    1. ox.graph_from_place → do thi NetworkX (MultiDiGraph)
    2. ox.add_edge_speeds → them thuoc tinh speed_kph cho moi canh
    3. ox.add_edge_travel_times → them thuoc tinh travel_time (giay)
    4. Luu cache bang pickle de lan sau khong can tai lai

    Tham so:
        ten_thanh_pho: Ten vung/thanh pho (vd: "Vinh, Nghe An, Vietnam")
        ban_kinh_m:    Ban kinh tai ban do tinh tu trung tam (met)

    Tra ve:
        G: nx.MultiDiGraph voi cac thuoc tinh length(m), speed_kph, travel_time(s)
    """
    import osmnx as ox

    in_thong_bao(f"Dang tai do thi: {ten_thanh_pho}")
    in_thong_bao(f"Ban kinh: {ban_kinh_m}m")
    in_canh_bao("Buoc nay co the mat 1-3 phut lan dau (tai tu OSM server)...")

    # Tai do thi duong xe hoi tu OSMnx
    G = ox.graph_from_place(
        ten_thanh_pho,
        network_type="drive"
    )

    # Them toc do (km/h) va thoi gian di chuyen (giay) cho tung canh
    G = ox.add_edge_speeds(G)
    G = ox.add_edge_travel_times(G)

    in_ket_qua(f"Da tai do thi: {len(G.nodes):,} nut | {len(G.edges):,} canh")
    return G


def main():
    in_tieu_de("TAI BAN DO DUONG PHO TU OPENSTREETMAP")

    # 1. Doc cau hinh
    if not os.path.exists(FILE_CAU_HINH):
        in_loi(f"Khong tim thay: {FILE_CAU_HINH}")
        return

    with open(FILE_CAU_HINH, "r", encoding="utf-8") as f:
        cau_hinh = json.load(f)

    ten_tp = cau_hinh["ten_thanh_pho"]
    ban_kinh = cau_hinh["ban_kinh_ban_do_m"]

    # 2. Kiem tra cache
    if os.path.exists(FILE_CACHE):
        in_thong_bao(f"Da tim thay cache: {FILE_CACHE}")
        in_thong_bao("Bo qua tai lai. Xoa file cache neu muon tai moi.")

        # Load de hien thi thong tin
        with open(FILE_CACHE, "rb") as f:
            data = pickle.load(f)
        G = data["graph"]
        in_ket_qua(f"Do thi trong cache: {len(G.nodes):,} nut | {len(G.edges):,} canh")
        return

    # 3. Tai ban do moi
    G = tai_ban_do_osm(ten_tp, ban_kinh)

    # 4. Luu cache
    os.makedirs(os.path.dirname(FILE_CACHE), exist_ok=True)
    cache_data = {
        "graph": G,
        "ten_thanh_pho": ten_tp,
        "ban_kinh_m": ban_kinh
    }
    with open(FILE_CACHE, "wb") as f:
        pickle.dump(cache_data, f)

    in_ket_qua(f"Da luu cache: {FILE_CACHE}")
    in_thong_bao("Lan chay sau se load tu cache, khong tai lai tu OSM.")


if __name__ == "__main__":
    main()
