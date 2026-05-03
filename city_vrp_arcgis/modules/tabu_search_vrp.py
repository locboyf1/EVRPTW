import copy
import random
from typing import List, Tuple, Dict
import numpy as np
from giao_dien.terminal_ui import in_tieu_de, in_thong_bao, in_tien_trinh, in_ket_qua

class TabuSearchVRPSolver:
    def __init__(self, so_xe, tai_trong_toi_da, luong_tai_xe, danh_sach_khach_hang, 
                 ma_tran_chi_phi_od, ma_tran_khi_thai_od, ma_tran_thoi_gian_od, 
                 toi_da_vong_lap=300, do_dai_tabu=15, alpha_weight=0.5, beta_weight=0.5):
        self.so_xe = so_xe
        self.tai_trong_toi_da = tai_trong_toi_da
        self.luong_tai_xe_phut = luong_tai_xe / 60.0
        self.khach_hang = danh_sach_khach_hang
        self.so_khach_hang = len(danh_sach_khach_hang)
        self.ma_tran_chi_phi = ma_tran_chi_phi_od
        self.ma_tran_khi_thai = ma_tran_khi_thai_od
        self.ma_tran_thoi_gian = ma_tran_thoi_gian_od
        self.toi_da_vong_lap = toi_da_vong_lap
        self.do_dai_tabu = do_dai_tabu
        self.alpha = alpha_weight
        self.beta = beta_weight
        self.tabu_list = []
        self.lo_trinh_tot_nhat = None
        self.f_tot_nhat = float('inf')

    def _danh_gia_mot_xe(self, lo_trinh: List[int]) -> Tuple[float, float, bool]:
        if not lo_trinh: return 0.0, 0.0, True
        tong_hang, tong_chi_phi, tong_khi_thai, thoi_gian_hien_tai, vi_tri_truoc = 0.0, 0.0, 0.0, 0.0, 0
        for kh_idx in lo_trinh:
            tong_hang += self.khach_hang[kh_idx].get('nhu_cau', 0)
        if tong_hang > self.tai_trong_toi_da: return float('inf'), float('inf'), False
        for kh_idx in lo_trinh:
            kh = self.khach_hang[kh_idx]
            curr_idx = kh_idx + 1
            tg_di = self.ma_tran_thoi_gian[vi_tri_truoc][curr_idx]
            thoi_gian_den = thoi_gian_hien_tai + tg_di
            if thoi_gian_den > kh['thoi_gian_dong_cua']: return float('inf'), float('inf'), False
            if thoi_gian_den < kh['thoi_gian_mo_cua']:
                tong_chi_phi += (kh['thoi_gian_mo_cua'] - thoi_gian_den) * self.luong_tai_xe_phut
                thoi_gian_den = kh['thoi_gian_mo_cua']
            thoi_gian_hien_tai = thoi_gian_den + kh['thoi_gian_boc_do']
            tong_chi_phi += self.ma_tran_chi_phi[vi_tri_truoc][curr_idx]
            tong_khi_thai += self.ma_tran_khi_thai[vi_tri_truoc][curr_idx]
            vi_tri_truoc = curr_idx
        tong_chi_phi += self.ma_tran_chi_phi[vi_tri_truoc][0]
        tong_khi_thai += self.ma_tran_khi_thai[vi_tri_truoc][0]
        return tong_chi_phi, tong_khi_thai, True

    def _tinh_tong_global(self, solution):
        global_cp, global_kt = 0.0, 0.0
        for r in solution:
            cp, kt, ok = self._danh_gia_mot_xe(r)
            if not ok: return float('inf'), 0, 0, False
            global_cp += cp
            global_kt += kt
        return self.alpha * global_cp + self.beta * global_kt, global_cp, global_kt, True

    def toan_tu_rut_cam(self, s):
        new_s = copy.deepcopy(s)
        avail = [i for i, r in enumerate(new_s) if r]
        if not avail: return new_s
        xe_a = random.choice(avail)
        xe_b = random.randrange(self.so_xe)
        kh_idx = new_s[xe_a].pop(random.randrange(len(new_s[xe_a])))
        new_s[xe_b].insert(random.randint(0, len(new_s[xe_b])), kh_idx)
        return new_s

    def toan_tu_doi_cheo(self, s):
        new_s = copy.deepcopy(s)
        avail = [i for i, r in enumerate(new_s) if r]
        if len(avail) < 2: return new_s
        xe_a, xe_b = random.sample(avail, 2)
        idx_a, idx_b = random.randrange(len(new_s[xe_a])), random.randrange(len(new_s[xe_b]))
        new_s[xe_a][idx_a], new_s[xe_b][idx_b] = new_s[xe_b][idx_b], new_s[xe_a][idx_a]
        return new_s

    def giai(self):
        in_tieu_de("TABU SEARCH VRP SOLVER")
        solution = [[] for _ in range(self.so_xe)]
        kh_idx = list(range(self.so_khach_hang))
        kh_idx.sort(key=lambda x: self.khach_hang[x].get('thoi_gian_mo_cua', 0))
        for i, idx in enumerate(kh_idx): solution[i % self.so_xe].append(idx)
        self.f_tot_nhat, _, _, _ = self._tinh_tong_global(solution)
        self.lo_trinh_tot_nhat = copy.deepcopy(solution)

        for v in range(self.toi_da_vong_lap):
            best_lc, f_best_lc = None, float('inf')
            for _ in range(40):
                lc = self.toan_tu_rut_cam(solution) if random.random() < 0.6 else self.toan_tu_doi_cheo(solution)
                f, _, _, ok = self._tinh_tong_global(lc)
                if ok and str(lc) not in self.tabu_list and f < f_best_lc:
                    f_best_lc, best_lc = f, lc
            if best_lc:
                solution = best_lc
                self.tabu_list.append(str(best_lc))
                if len(self.tabu_list) > self.do_dai_tabu: self.tabu_list.pop(0)
                if f_best_lc < self.f_tot_nhat:
                    self.f_tot_nhat, self.lo_trinh_tot_nhat = f_best_lc, copy.deepcopy(best_lc)
            if v % 20 == 0: in_tien_trinh(v/self.toi_da_vong_lap*100, f"Vòng {v}/{self.toi_da_vong_lap}")
        return self._xuat_ket_qua()

    def _xuat_ket_qua(self):
        f, cp, kt, _ = self._tinh_tong_global(self.lo_trinh_tot_nhat)
        res = {"ham_muc_tieu": f, "tong_chi_phi": cp, "tong_khi_thai": kt, "lo_trinh": {}}
        for i, r in enumerate(self.lo_trinh_tot_nhat):
            if r: res["lo_trinh"][f"Xe_{i+1:02d}"] = {"mo_ta": " -> ".join(["[Kho]"] + [self.khach_hang[k]['ten'] for k in r] + ["[Kho]"]), "thu_tu": r}
        in_ket_qua(f"DONE - CP: ${cp:.2f} | KT: {kt:.2f}g")
        return res
