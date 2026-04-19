import os
import sys
import time
import json
import numpy as np

# Them duong dan goc vao he thong de co the import cac lop con
_THU_MUC_GOC = os.path.dirname(os.path.abspath(__file__))
if _THU_MUC_GOC not in sys.path:
    sys.path.insert(0, _THU_MUC_GOC)

# Import tu lop 1: Tien xu ly
from lop_1_tien_xu_ly.tao_du_lieu import doc_json, luu_lich_su_chay

# Import tu lop 2: Network Analyst
from lop_2_network_analyst.dijkstra_ma_tran_od import (
    tai_ban_do_osm, snap_diem_vao_do_thi, tao_ma_tran_od_bang_dijkstra
)

# Import tu lop 3: VRP Solver
from lop_3_vrp_solver.tabu_search_vrp import TabuSearchVRPSolver

# Giao dien
from giao_dien.terminal_ui import (
    in_tieu_de, in_thong_bao, in_canh_bao
)

# =============================================================================
# CAU HINH HE THONG (Wygonik & Goodchild 2010 Blueprint)
# =============================================================================
CAU_HINH = {
    "ten_thanh_pho": "Vinh, Nghe An, Vietnam",
    "ban_kinh_m":    6000,
    "so_xe":         17,
    "tai_trong_max": 90,
    "luong_tai_xe":  26.55,
    "he_so_mo_phong_hybrid": 0.6,
    "vong_lap_tabu": 300,
    "ten_kich_ban":  "Density"
}

def chay_he_thong():
    os.system('cls' if os.name == 'nt' else 'clear')
    in_tieu_de("CITY VRP -- PHIEN BAN GIAO TRINH (REFACTORED V6)")

    # -------------------------------------------------------------------------
    # GIAI DOAN 1: DOC DU LIEU
    # -------------------------------------------------------------------------
    print("\n[LOP 1] DANG NAP DU LIEU...")
    du_lieu_dir = os.path.join(_THU_MUC_GOC, "du_lieu")
    
    kt_json = doc_json(os.path.join(du_lieu_dir, "du_lieu_khi_thai.json"))
    xe_json = doc_json(os.path.join(du_lieu_dir, "cau_hinh_xe.json"))
    kh_json = doc_json(os.path.join(du_lieu_dir, "khach_hang.json"))
    
    kho = kh_json["kho_xuat_phat"]
    khach_hang = kh_json["danh_sach_khach_hang"]
    tat_ca_diem = [kho] + khach_hang
    
    # Lay dung tu dien bang_moves
    bang_moves = kt_json["bang_moves"]
    xe_mau = next((x for x in xe_json["danh_sach_xe"] if x["ma_xe"] == "XE_01"), xe_json["danh_sach_xe"][0])
    
    in_thong_bao(f"  OK - Da nap {len(khach_hang)} khach hang tai vung mo phong.")

    # -------------------------------------------------------------------------
    # GIAI DOAN 2: MA TRAN OD (DIJKSTRA)
    # -------------------------------------------------------------------------
    print("\n[LOP 2] DANG TINH TOAN MA TRAN OD (OSMNX + DIJKSTRA)...")
    G, dung_osm = tai_ban_do_osm(CAU_HINH["ten_thanh_pho"], CAU_HINH["ban_kinh_m"], tat_ca_diem=tat_ca_diem)
    
    nodes_id = snap_diem_vao_do_thi(G, tat_ca_diem, dung_osmnx=dung_osm)
    
    # Chạy Dijkstra
    ma_tran_cp, ma_tran_kt, ma_tran_tg, ma_tran_km = tao_ma_tran_od_bang_dijkstra(
        G, nodes_id, xe_mau, CAU_HINH["luong_tai_xe"], bang_moves
    )

    # Quy doi don vi: Dijkstra tra ve Giay -> Quy doi sang Phut de khop voi Time Window
    ma_tran_tg = ma_tran_tg / 60.0
    in_thong_bao("  OK - Da quy doi ma tran thoi gian sang phut.")

    # Nhan he so Hybrid
    ma_tran_kt_final = ma_tran_kt * CAU_HINH["he_so_mo_phong_hybrid"]
    in_thong_bao(f"  OK - Da ap dung he so Hybrid {CAU_HINH['he_so_mo_phong_hybrid']} vao khi thai.")

    # -------------------------------------------------------------------------
    # GIAI DOAN 3: TABU SEARCH
    # -------------------------------------------------------------------------
    solver = TabuSearchVRPSolver(
        so_xe=CAU_HINH["so_xe"],
        tai_trong_toi_da=CAU_HINH["tai_trong_max"],
        luong_tai_xe=CAU_HINH["luong_tai_xe"],
        danh_sach_khach_hang=khach_hang,
        ma_tran_chi_phi_od=ma_tran_cp,
        ma_tran_khi_thai_od=ma_tran_kt_final,
        ma_tran_thoi_gian_od=ma_tran_tg,
        toi_da_vong_lap=CAU_HINH["vong_lap_tabu"]
    )
    
    ket_qua = solver.giai()

    # -------------------------------------------------------------------------
    # TONG KET & LUU LICH SU
    # -------------------------------------------------------------------------
    # A. Luu file JSON chi tiet
    output_json = os.path.join(_THU_MUC_GOC, "ket_qua_v6.json")
    with open(output_json, "w", encoding="utf-8") as f:
        json.dump(ket_qua, f, ensure_ascii=False, indent=4)
        
    # B. Luu file CSV lich su (Phuc vu truc quan hoa)
    log_data = {
        "Thanh_Pho": CAU_HINH["ten_thanh_pho"],
        "So_Khach":  len(khach_hang),
        "Alpha":     0.5, # Mac dinh ty le quan trong
        "Beta":      0.5,
        "Chi_Phi":   ket_qua.get("tong_chi_phi", 0),
        "Khi_Thai":  ket_qua.get("tong_khi_thai", 0),
        "Kich_Ban":  CAU_HINH["ten_kich_ban"]
    }
    file_csv = os.path.join(du_lieu_dir, "lich_su_chay.csv")
    luu_lich_su_chay(file_csv, log_data)
    
    print("\n" + "="*60)
    print("      HE THONG MO PHONG HOAN THANH!")
    print(f"      Ket qua JSON: {output_json}")
    print(f"      Lich su CSV:  {file_csv}")
    print("="*60)

if __name__ == "__main__":
    try:
        chay_he_thong()
    except Exception as e:
        in_canh_bao(f"Loi: {e}")
        import traceback
        traceback.print_exc()
