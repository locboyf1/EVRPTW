import sys
import os
import networkx as nx
import numpy as np

try:
    import osmnx as ox
    OSMNX_CO_SAN = True
except ImportError:
    OSMNX_CO_SAN = False

# Import UI local
from giao_dien.terminal_ui import in_tieu_de, in_thong_bao, in_canh_bao, in_tien_trinh

TOC_DO_MAC_DINH_KM_H       = 50
HANG_SO_KHI_THAI_MAC_DINH  = 0.261

def _tao_do_thi_du_phong(tat_ca_diem: list) -> nx.DiGraph:
    import math
    in_canh_bao("Đang dùng đồ thị giả (Euclidean) vì OSMnx không khả dụng!")
    G = nx.DiGraph()
    for i, diem in enumerate(tat_ca_diem):
        G.add_node(i, x=diem["kinh_do"], y=diem["vi_do"])
    DO_KHUECH_DAI_KM_PER_DO = 111.0
    for i in range(len(tat_ca_diem)):
        for j in range(len(tat_ca_diem)):
            if i == j: continue
            di, dj = tat_ca_diem[i], tat_ca_diem[j]
            dx = (dj["kinh_do"] - di["kinh_do"]) * DO_KHUECH_DAI_KM_PER_DO * 1000
            dy = (dj["vi_do"]   - di["vi_do"])   * DO_KHUECH_DAI_KM_PER_DO * 1000
            length_m = math.sqrt(dx * dx + dy * dy)
            toc_do_ms = TOC_DO_MAC_DINH_KM_H * 1000 / 3600
            travel_time_s = length_m / toc_do_ms if toc_do_ms > 0 else 0
            G.add_edge(i, j, length=length_m, speed_kph=TOC_DO_MAC_DINH_KM_H, travel_time=travel_time_s)
    return G

def tai_ban_do_osm(ten_thanh_pho: str, ban_kinh_met: int, tat_ca_diem: list = None):
    if not OSMNX_CO_SAN:
        return _tao_do_thi_du_phong(tat_ca_diem), False
    try:
        do_thi = ox.graph_from_address(ten_thanh_pho, network_type="drive", dist=ban_kinh_met)
        do_thi = ox.add_edge_speeds(do_thi)
        do_thi = ox.add_edge_travel_times(do_thi)
        return do_thi, True
    except Exception as e:
        in_canh_bao(f"Lỗi tải OSM: {e}")
        return _tao_do_thi_du_phong(tat_ca_diem), False

def snap_diem_vao_do_thi(do_thi, tat_ca_diem: list, dung_osmnx: bool = True):
    if not dung_osmnx:
        return list(range(len(tat_ca_diem)))
    danh_sach_node = []
    for diem in tat_ca_diem:
        node = ox.distance.nearest_nodes(do_thi, X=diem["kinh_do"], Y=diem["vi_do"])
        danh_sach_node.append(node)
    return danh_sach_node

def tao_ma_tran_od_bang_dijkstra(do_thi, danh_sach_node_osm, cau_hinh_xe, luong_tai_xe, bang_moves):
    so_diem = len(danh_sach_node_osm)
    chi_phi_hao_mon_per_km = cau_hinh_xe["chi_phi_hao_mon_usd_per_km"]
    
    ma_tran_cp = np.zeros((so_diem, so_diem))
    ma_tran_kt = np.zeros((so_diem, so_diem))
    ma_tran_tg = np.zeros((so_diem, so_diem))
    ma_tran_km = np.zeros((so_diem, so_diem))

    for i, node_nguon in enumerate(danh_sach_node_osm):
        try:
            _, paths_dict = nx.single_source_dijkstra(do_thi, source=node_nguon, weight="travel_time")
        except: continue
        
        for j, node_dich in enumerate(danh_sach_node_osm):
            if i == j: continue
            try:
                if node_dich not in paths_dict: raise nx.NetworkXNoPath
                duong_di = paths_dict[node_dich]
                l_m, t_s = 0.0, 0.0
                for k in range(len(duong_di) - 1):
                    canh = do_thi[duong_di[k]][duong_di[k+1]]
                    if isinstance(do_thi, nx.MultiDiGraph):
                        canh = min(canh.values(), key=lambda c: c.get("travel_time", float("inf")))
                    l_m += canh.get("length", 0)
                    t_s += canh.get("travel_time", 0)
                
                l_km = l_m / 1000.0
                t_h = t_s / 3600.0
                v_kmh = l_km / t_h if t_h > 0 else TOC_DO_MAC_DINH_KM_H
                v_tra = max(20, min(120, round(v_kmh / 10) * 10))
                he_so_kt = bang_moves.get(v_tra, HANG_SO_KHI_THAI_MAC_DINH)
                
                ma_tran_cp[i][j] = l_km * chi_phi_hao_mon_per_km + t_h * luong_tai_xe
                ma_tran_kt[i][j] = l_km * he_so_kt
                ma_tran_tg[i][j] = t_s
                ma_tran_km[i][j] = l_km
            except:
                ma_tran_cp[i][j] = ma_tran_kt[i][j] = ma_tran_tg[i][j] = ma_tran_km[i][j] = 1e9
        in_tien_trinh((i+1)/so_diem*100, f"Dijkstra: {i+1}/{so_diem}")
    return ma_tran_cp, ma_tran_kt, ma_tran_tg, ma_tran_km
