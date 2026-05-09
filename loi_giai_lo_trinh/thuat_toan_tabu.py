"""
=============================================================
LOI GIAI LO TRINH: TABU SEARCH VRP SOLVER
=============================================================
LUONG DU LIEU:
    Ma_Tran_OD.npz ──LOAD──▶ [SCRIPT NAY] ──▶ ket_qua_tabu.json
    khach_hang.json ─────────┘

NGUYEN TAC BAT BIEN:
    - CHI doc ma tran OD tu file .npz (giao tiep qua file vat ly)
    - KHONG BAO GIO import tu loi_giai_mang_luoi
    - RANG BUOC 8 TIENG (480 phut) trong _danh_gia_mot_xe

CHE DO CHAY (so_luong_service_windows):
    - 1 (Scenario 1): Gop chung, chay Tabu 1 lan, CSV 1 dong
    - 3 (Baseline):   Chay 3 lan (PreDawn/Breakfast/Lunch-Dinner),
                      CSV 3 dong, JSON 3 key
=============================================================
"""

import os, sys, json, csv, copy, random, math
from datetime import datetime
from typing import List, Tuple, Dict, Optional
import numpy as np

_THU_MUC_SCRIPT = os.path.dirname(os.path.abspath(__file__))
_THU_MUC_GOC = os.path.dirname(_THU_MUC_SCRIPT)
if _THU_MUC_GOC not in sys.path:
    sys.path.insert(0, _THU_MUC_GOC)

from giao_dien.terminal_ui import (
    in_tieu_de, in_thong_bao, in_canh_bao, in_tien_trinh, in_ket_qua, in_loi
)

FILE_CAU_HINH    = os.path.join(_THU_MUC_GOC, "cau_hinh", "cau_hinh_co_so.json")
FILE_MA_TRAN_NPZ = os.path.join(_THU_MUC_GOC, "du_lieu", "Ma_Tran_OD.npz")
FILE_KHACH_HANG  = os.path.join(_THU_MUC_GOC, "du_lieu", "khach_hang.json")
FILE_KET_QUA     = os.path.join(_THU_MUC_GOC, "du_lieu", "ket_qua_tabu.json")
FILE_CSV         = os.path.join(_THU_MUC_GOC, "du_lieu", "lich_su_so_sanh.csv")


# ─────────────────────────────────────────────────────────────
# HAM PHU TRO
# ─────────────────────────────────────────────────────────────
def time_to_minutes(hh_mm_str: str) -> int:
    h, m = hh_mm_str.split(":")
    return int(h) * 60 + int(m)


def _xac_dinh_ca(thoi_gian_mo_cua_hhmm: str, ds_ca: dict) -> str:
    """
    Suy ra ten ca tu thoi_gian_mo_cua (HH:MM) bang cach doi chieu
    voi ranh gioi bat_dau/ket_thuc cua tung ca trong cau hinh.
    """
    mo_phut = time_to_minutes(thoi_gian_mo_cua_hhmm)
    for ten_ca, cfg in ds_ca.items():
        bat_dau = time_to_minutes(cfg["bat_dau"])
        ket_thuc = time_to_minutes(cfg["ket_thuc"])
        if bat_dau <= mo_phut < ket_thuc:
            return ten_ca
    return "Unknown"


# ═══════════════════════════════════════════════════════════
# CLASS CHINH: TABU SEARCH VRP SOLVER
# ═══════════════════════════════════════════════════════════
class TabuSearchVRPSolver:
    def __init__(self, so_xe, tai_trong_toi_da, gio_han_lam_viec_phut,
                 luong_tai_xe, danh_sach_khach_hang,
                 ma_tran_chi_phi, ma_tran_khi_thai, ma_tran_thoi_gian,
                 toi_da_vong_lap=300, do_dai_tabu=15,
                 trong_so_chi_phi=0.5, trong_so_khi_thai=0.5):
        self.so_xe = so_xe
        self.tai_trong_toi_da = tai_trong_toi_da
        self.gio_han_phut = gio_han_lam_viec_phut
        self.luong_tai_xe_phut = luong_tai_xe / 60.0
        self.khach_hang = danh_sach_khach_hang  # FULL list (giu index goc)
        self.so_khach_hang = len(danh_sach_khach_hang)
        self.ma_tran_chi_phi = ma_tran_chi_phi
        self.ma_tran_khi_thai = ma_tran_khi_thai
        self.ma_tran_thoi_gian = ma_tran_thoi_gian
        self.toi_da_vong_lap = toi_da_vong_lap
        self.do_dai_tabu = do_dai_tabu
        self.alpha = trong_so_chi_phi
        self.beta = trong_so_khi_thai
        self.tabu_list: List[str] = []
        self.lo_trinh_tot_nhat: Optional[List[List[int]]] = None
        self.f_tot_nhat = float('inf')
        self.so_kh_hien_tai = self.so_khach_hang

    # ─────────────────────────────────────────────────────────
    # DANH GIA MOT XE
    # ─────────────────────────────────────────────────────────
    def _danh_gia_mot_xe(self, lo_trinh: List[int]) -> Tuple[float, float, bool]:
        if not lo_trinh:
            return 0.0, 0.0, True
        tong_hang = sum(self.khach_hang[k].get('nhu_cau', 0) for k in lo_trinh)
        if tong_hang > self.tai_trong_toi_da:
            return float('inf'), float('inf'), False
        tong_cp, tong_kt = 0.0, 0.0
        tg_ht = 0.0
        vt_truoc = 0
        for kh_idx in lo_trinh:
            kh = self.khach_hang[kh_idx]
            idx_mt = kh_idx + 1  # Index ma tran OD — GIU NGUYEN vi dung index goc
            tg_dd = self.ma_tran_thoi_gian[vt_truoc][idx_mt]
            cp_c = self.ma_tran_chi_phi[vt_truoc][idx_mt]
            kt_c = self.ma_tran_khi_thai[vt_truoc][idx_mt]
            if cp_c == float('inf') or np.isinf(cp_c):
                return float('inf'), float('inf'), False
            tg_den = tg_ht + tg_dd
            if tg_den > kh['thoi_gian_dong_cua']:
                return float('inf'), float('inf'), False
            if tg_den < kh['thoi_gian_mo_cua']:
                tong_cp += (kh['thoi_gian_mo_cua'] - tg_den) * self.luong_tai_xe_phut
                tg_den = kh['thoi_gian_mo_cua']
            tg_ht = tg_den + kh['thoi_gian_boc_do']
            tong_cp += kh['thoi_gian_boc_do'] * self.luong_tai_xe_phut
            tong_cp += cp_c
            tong_kt += kt_c
            vt_truoc = idx_mt
        tg_ht += self.ma_tran_thoi_gian[vt_truoc][0]
        tong_cp += self.ma_tran_chi_phi[vt_truoc][0]
        tong_kt += self.ma_tran_khi_thai[vt_truoc][0]
        if tg_ht > self.gio_han_phut:
            return float('inf'), float('inf'), False
        return tong_cp, tong_kt, True

    def _tinh_tong_global(self, solution):
        g_cp, g_kt = 0.0, 0.0
        for r in solution:
            cp, kt, ok = self._danh_gia_mot_xe(r)
            if not ok:
                return float('inf'), 0, 0, False
            g_cp += cp
            g_kt += kt
        return self.alpha * g_cp + self.beta * g_kt, g_cp, g_kt, True

    # ─────────────────────────────────────────────────────────
    # TOAN TU LANG GIENG
    # ─────────────────────────────────────────────────────────
    def _toan_tu_rut_cam(self, s):
        ns = copy.deepcopy(s)
        avail = [i for i, r in enumerate(ns) if r]
        if len(avail) < 1:
            return ns
        xa = random.choice(avail)
        xb = random.choice(range(self.so_xe))
        kh = ns[xa].pop(random.randrange(len(ns[xa])))
        ns[xb].insert(random.randint(0, len(ns[xb])), kh)
        return ns

    def _toan_tu_doi_cheo(self, s):
        ns = copy.deepcopy(s)
        avail = [i for i, r in enumerate(ns) if r]
        if len(avail) < 2:
            return ns
        xa, xb = random.sample(avail, 2)
        ia, ib = random.randrange(len(ns[xa])), random.randrange(len(ns[xb]))
        ns[xa][ia], ns[xb][ib] = ns[xb][ib], ns[xa][ia]
        return ns

    # ─────────────────────────────────────────────────────────
    # VONG LAP CHINH — NHAN tap_khach_hang_index
    # ─────────────────────────────────────────────────────────
    def giai(self, tap_khach_hang_index: List[int] = None) -> Dict:
        """
        Giai Tabu Search cho TAP CON khach hang.

        tap_khach_hang_index: danh sach INDEX GOC trong self.khach_hang.
            Vi du: [0, 5, 8, 12] — chi giao hang cho 4 KH nay.
            idx_mt = kh_idx + 1 van dung vi dung index goc.

        Neu None → lay toan bo range(so_khach_hang).
        """
        if tap_khach_hang_index is None:
            tap_khach_hang_index = list(range(self.so_khach_hang))

        self.so_kh_hien_tai = len(tap_khach_hang_index)

        in_tieu_de("LOI GIAI LO TRINH: TABU SEARCH")
        in_thong_bao(f"So KH trong tap: {self.so_kh_hien_tai} / {self.so_khach_hang} tong")
        in_thong_bao(f"So xe: {self.so_xe} | Tai trong max: {self.tai_trong_toi_da}")
        in_thong_bao(f"Gioi han: {self.gio_han_phut} phut | Vong lap: {self.toi_da_vong_lap}")

        # ── Khoi tao: sap xep theo gio mo cua ──
        solution = [[] for _ in range(self.so_xe)]
        kh_list = sorted(tap_khach_hang_index,
                         key=lambda x: self.khach_hang[x].get('thoi_gian_mo_cua', 0))
        for i, kh in enumerate(kh_list):
            solution[i % self.so_xe].append(kh)

        f_best, cp_best, kt_best, ok = self._tinh_tong_global(solution)
        if not ok:
            in_canh_bao("Loi giai ban dau INFEASIBLE! Dang thu xao tron...")
            random.shuffle(kh_list)
            solution = [[] for _ in range(self.so_xe)]
            for i, kh in enumerate(kh_list):
                solution[i % self.so_xe].append(kh)
            f_best, cp_best, kt_best, _ = self._tinh_tong_global(solution)

        self.lo_trinh_tot_nhat = copy.deepcopy(solution)
        self.f_tot_nhat = f_best
        self.tabu_list = []
        in_thong_bao(f"Khoi tao: F={f_best:.4f}")

        # ── Vong lap Tabu ──
        for vong in range(self.toi_da_vong_lap):
            tap_lc = []
            for _ in range(40):
                if random.random() < 0.6:
                    tap_lc.append(self._toan_tu_rut_cam(solution))
                else:
                    tap_lc.append(self._toan_tu_doi_cheo(solution))
            best_lc, f_best_lc = None, float('inf')
            for lc in tap_lc:
                f, cp, kt, ok = self._tinh_tong_global(lc)
                sk = str(lc)
                if ok and sk not in self.tabu_list and f < f_best_lc:
                    f_best_lc, best_lc = f, lc
            if best_lc:
                solution = best_lc
                self.tabu_list.append(str(best_lc))
                if len(self.tabu_list) > self.do_dai_tabu:
                    self.tabu_list.pop(0)
                if f_best_lc < self.f_tot_nhat:
                    self.f_tot_nhat = f_best_lc
                    self.lo_trinh_tot_nhat = copy.deepcopy(best_lc)
                    in_thong_bao(f"  Vong {vong}: F = {self.f_tot_nhat:.4f}")
            if vong % 20 == 0:
                in_tien_trinh(vong / self.toi_da_vong_lap * 100,
                              f"Tabu ({vong}/{self.toi_da_vong_lap})")

        in_tien_trinh(100, "Tabu Search HOAN THANH")
        return self._xuat_ket_qua()

    # ─────────────────────────────────────────────────────────
    # XUAT KET QUA — dung so_kh_hien_tai cho Per Order
    # ─────────────────────────────────────────────────────────
    def _xuat_ket_qua(self) -> Dict:
        f, cp, kt, _ = self._tinh_tong_global(self.lo_trinh_tot_nhat)
        n = self.so_kh_hien_tai
        cp_po = cp / n if n > 0 else 0.0
        kt_po = kt / n if n > 0 else 0.0
        so_xe_dung = sum(1 for r in self.lo_trinh_tot_nhat if r)
        boc_do = self.khach_hang[0].get("thoi_gian_boc_do", 10) if self.so_khach_hang > 0 else 10
        res = {
            "ham_muc_tieu": float(f), "tong_chi_phi": float(cp),
            "tong_khi_thai": float(kt), "chi_phi_per_order": float(cp_po),
            "khi_thai_per_order": float(kt_po), "so_xe_dung": so_xe_dung,
            "thoi_gian_boc_do_phut": boc_do, "so_khach_hang_trong_tap": n,
            "lo_trinh": {}
        }
        for i, r in enumerate(self.lo_trinh_tot_nhat):
            if not r:
                continue
            ten_kh = [self.khach_hang[k]['ten'] for k in r]
            res["lo_trinh"][f"Xe_{i+1:02d}"] = {
                "mo_ta": " -> ".join(["[Kho]"] + ten_kh + ["[Kho]"]),
                "thu_tu": r
            }
        in_ket_qua(f"Cost: ${cp:.2f} (${cp_po:.2f}/order) | "
                    f"Emit: {kt:.2f}g ({kt_po:.2f}g/order) | "
                    f"Xe: {so_xe_dung}/{self.so_xe}")
        return res


# ─────────────────────────────────────────────────────────────
# CSV HELPER
# ─────────────────────────────────────────────────────────────
CSV_HEADER = [
    "Lan_Chay", "Thoi_Gian", "Ten_Kich_Ban", "Ca_Hoat_Dong", "Che_Do_TW",
    "Do_Rong_TW", "So_Khach", "Tai_Trong", "T.Gian_Boc_Do", "So_Xe_Dung",
    "Chi_Phi_Tong", "Khi_Thai_Tong", "Chi_Phi_Per_Order", "Khi_Thai_Per_Order"
]

def _ghi_csv(lan_chay_id, cau_hinh, profile_xe, ten_ca_label, so_kh, ket_qua):
    """Ghi 1 dong vao lich_su_so_sanh.csv (14 cot)."""
    file_ton_tai = os.path.isfile(FILE_CSV)
    with open(FILE_CSV, "a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if not file_ton_tai:
            w.writerow(CSV_HEADER)
        w.writerow([
            lan_chay_id,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            cau_hinh["ten_kich_ban"],
            ten_ca_label,
            cau_hinh["che_do_time_window"],
            cau_hinh["do_rong_cua_so_phut"],
            so_kh,
            profile_xe["tai_trong"],
            cau_hinh["thoi_gian_boc_do_phut"],
            ket_qua["so_xe_dung"],
            round(ket_qua["tong_chi_phi"], 2),
            round(ket_qua["tong_khi_thai"], 2),
            round(ket_qua["chi_phi_per_order"], 4),
            round(ket_qua["khi_thai_per_order"], 4)
        ])


# ─────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────
def main():
    in_tieu_de("KHOI CHAY DOC LAP: TABU SEARCH")

    # ── Tao ma dinh danh duy nhat cho lan chay nay ──
    lan_chay_id = datetime.now().strftime("%Y%m%d_%H%M%S")

    # 1. Doc cau hinh
    with open(FILE_CAU_HINH, "r", encoding="utf-8") as f:
        cau_hinh = json.load(f)

    so_sw = cau_hinh["so_luong_service_windows"]
    ds_ca = cau_hinh["danh_sach_ca_hoat_dong"]
    tham_so = cau_hinh["tham_so_tabu"]

    # Lay thong so xe tu profile duoc chon
    loai_xe = cau_hinh["loai_xe_su_dung"]
    profile_xe = cau_hinh["danh_sach_xe"][loai_xe]

    in_thong_bao(f"Lan chay: {lan_chay_id}")
    in_thong_bao(f"Kich ban: {cau_hinh['ten_kich_ban']} | Loai xe: {loai_xe}")
    in_thong_bao(f"Service Windows = {so_sw} ({'Scenario 1 — Gop ca' if so_sw == 1 else 'Baseline — 3 ca'})")

    # 2. Load ma tran OD
    if not os.path.exists(FILE_MA_TRAN_NPZ):
        in_loi(f"Khong tim thay: {FILE_MA_TRAN_NPZ}")
        return
    matrices = np.load(FILE_MA_TRAN_NPZ)

    # 3. Load khach hang
    with open(FILE_KHACH_HANG, "r", encoding="utf-8") as f:
        kh_json = json.load(f)
    khach_hang = kh_json["danh_sach_khach_hang"]

    # ══════════════════════════════════════════════════════════
    # 4. GAN NHAN CA + CHUYEN HH:MM → PHUT TUONG DOI
    # ──────────────────────────────────────────────────────────
    # Moi KH duoc gan "ca_hoat_dong" (suy tu thoi_gian_mo_cua).
    # Sau do chuyen thoi gian sang PHUT TUONG DOI (0 = dau ca)
    # de solver tinh toan dung voi gio_han_lam_viec_phut = 480.
    # ══════════════════════════════════════════════════════════
    for kh in khach_hang:
        # Suy ra ca neu chua co san
        if "ca_hoat_dong" not in kh:
            kh["ca_hoat_dong"] = _xac_dinh_ca(kh["thoi_gian_mo_cua"], ds_ca)

        # Lay offset cua ca nay
        ten_ca_kh = kh["ca_hoat_dong"]
        if ten_ca_kh in ds_ca:
            offset = time_to_minutes(ds_ca[ten_ca_kh]["bat_dau"])
        else:
            offset = 0

        # Chuyen HH:MM → phut tuong doi (chi chuyen neu con la chuoi)
        if isinstance(kh["thoi_gian_mo_cua"], str):
            kh["thoi_gian_mo_cua"] = time_to_minutes(kh["thoi_gian_mo_cua"]) - offset
            kh["thoi_gian_dong_cua"] = time_to_minutes(kh["thoi_gian_dong_cua"]) - offset

    # ══════════════════════════════════════════════════════════
    # 5. TAO SOLVER VA CHAY THEO so_luong_service_windows
    # ══════════════════════════════════════════════════════════
    def _tao_solver():
        return TabuSearchVRPSolver(
            so_xe=cau_hinh["so_xe"],
            tai_trong_toi_da=profile_xe["tai_trong"],
            gio_han_lam_viec_phut=cau_hinh["gio_han_lam_viec_phut"],
            luong_tai_xe=profile_xe["luong"],
            danh_sach_khach_hang=khach_hang,
            ma_tran_chi_phi=matrices['cp'],
            ma_tran_khi_thai=matrices['kt'],
            ma_tran_thoi_gian=matrices['tg'] / 60.0,
            toi_da_vong_lap=tham_so["toi_da_vong_lap"],
            do_dai_tabu=tham_so["do_dai_tabu"],
            trong_so_chi_phi=tham_so["trong_so_chi_phi"],
            trong_so_khi_thai=tham_so["trong_so_khi_thai"]
        )

    os.makedirs(os.path.dirname(FILE_KET_QUA), exist_ok=True)

    if so_sw == 1:
        # ────────────────────────────────────────────────────
        # SCENARIO 1: GOP CHUNG — chay 1 lan, CSV 1 dong
        # ────────────────────────────────────────────────────
        tap_idx = list(range(len(khach_hang)))
        in_thong_bao(f"Scenario 1: Gop chung {len(tap_idx)} KH")

        solver = _tao_solver()
        ket_qua = solver.giai(tap_khach_hang_index=tap_idx)

        # Luu JSON
        with open(FILE_KET_QUA, "w", encoding="utf-8") as f:
            json.dump({"All_Merged": ket_qua}, f, ensure_ascii=False, indent=4)
        in_ket_qua(f"Da luu JSON: {FILE_KET_QUA}")

        # Ghi CSV
        _ghi_csv(lan_chay_id, cau_hinh, profile_xe, "All_Merged", len(tap_idx), ket_qua)
        in_ket_qua(f"Da ghi CSV: {FILE_CSV}")

    elif so_sw == 3:
        # ────────────────────────────────────────────────────
        # BASELINE: CHAY 3 CA DOC LAP
        # ────────────────────────────────────────────────────
        ket_qua_tong = {}

        for ten_ca in ["PreDawn", "Breakfast", "Lunch/Dinner"]:
            # Loc index goc cua KH thuoc ca nay
            tap_idx = [i for i, kh in enumerate(khach_hang)
                       if kh.get("ca_hoat_dong") == ten_ca]

            if not tap_idx:
                in_canh_bao(f"Ca {ten_ca}: KHONG co KH nao — bo qua.")
                continue

            in_tieu_de(f"CA: {ten_ca} ({len(tap_idx)} KH)")

            solver = _tao_solver()
            kq = solver.giai(tap_khach_hang_index=tap_idx)
            ket_qua_tong[ten_ca] = kq

            # Ghi CSV cho ca nay (chung lan_chay_id)
            _ghi_csv(lan_chay_id, cau_hinh, profile_xe, ten_ca, len(tap_idx), kq)
            in_ket_qua(f"Da ghi CSV cho ca {ten_ca}")

        # Luu JSON tong (3 key, khong ghi de nhau)
        with open(FILE_KET_QUA, "w", encoding="utf-8") as f:
            json.dump(ket_qua_tong, f, ensure_ascii=False, indent=4)
        in_ket_qua(f"Da luu JSON (3 ca): {FILE_KET_QUA}")

    else:
        in_loi(f"so_luong_service_windows = {so_sw} khong hop le (chi chap nhan 1 hoac 3).")


if __name__ == "__main__":
    main()
