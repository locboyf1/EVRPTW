import sys
import os
import copy
import random
from typing import List, Tuple, Dict, Optional
import numpy as np

# Thêm đường dẫn gốc vào sys.path để import giao diện
_THU_MUC_GOC = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _THU_MUC_GOC not in sys.path:
    sys.path.insert(0, _THU_MUC_GOC)

from giao_dien.terminal_ui import (
    in_tieu_de, in_thong_bao, in_canh_bao, in_tien_trinh, in_ket_qua
)

class TabuSearchVRPSolver:
    """
    Thuật toán Tabu Search giải quyết bài toán VRPTW với đội xe 17 chiếc.
    Tuân thủ phương pháp luận của Wygonik & Goodchild (2010).
    """

    def __init__(self,
                 so_xe: int = 17,
                 tai_trong_toi_da: float = 90.0,
                 luong_tai_xe: float = 26.55, # Giá USD/giờ
                 danh_sach_khach_hang: list = [],
                 ma_tran_chi_phi_od: np.ndarray = None,
                 ma_tran_khi_thai_od: np.ndarray = None,
                 ma_tran_thoi_gian_od: np.ndarray = None,
                 toi_da_vong_lap: int = 300,
                 do_dai_tabu: int = 15,
                 alpha_weight: float = 0.5, # Trọng số chi phí
                 beta_weight: float = 0.5): # Trọng số khí thải
        
        self.so_xe = so_xe
        self.tai_trong_toi_da = tai_trong_toi_da
        self.luong_tai_xe_phut = luong_tai_xe / 60.0 # Quy đổi ra $/phút
        self.khach_hang = danh_sach_khach_hang
        self.so_khach_hang = len(danh_sach_khach_hang)
        
        # Ma trận OD (Tĩnh - được sinh ra từ lớp 2 Dijkstra)
        self.ma_tran_chi_phi = ma_tran_chi_phi_od
        self.ma_tran_khi_thai = ma_tran_khi_thai_od
        self.ma_tran_thoi_gian = ma_tran_thoi_gian_od
        
        # Tham số giải thuật
        self.toi_da_vong_lap = toi_da_vong_lap
        self.do_dai_tabu = do_dai_tabu
        self.alpha = alpha_weight
        self.beta = beta_weight
        
        self.tabu_list = []
        self.lo_trinh_tot_nhat = None
        self.f_tot_nhat = float('inf')

    # -------------------------------------------------------------------------
    # HÀM: ĐÁNH GIÁ LỘ TRÌNH CỦA MỘT XE (Bám sát Blueprint)
    # -------------------------------------------------------------------------
    def _danh_gia_mot_xe(self, lo_trinh: List[int]) -> Tuple[float, float, bool]:
        """
        Tính toán chi phí và khí thải cho 1 xe. Kiểm tra Tải trọng và Time Window.
        """
        if not lo_trinh: return 0.0, 0.0, True
        
        tong_hang = 0.0
        tong_chi_phi = 0.0
        tong_khi_thai = 0.0
        thoi_gian_hien_tai = 0.0 # Phút thứ 0
        vi_tri_truoc = 0 # Bắt đầu từ Kho (Index 0)

        # 1. Kiểm tra Tổng tải trọng TRƯỚC (Ràng buộc cứng)
        for kh_idx in lo_trinh:
            tong_hang += self.khach_hang[kh_idx].get('nhu_cau', 0)
        
        if tong_hang > self.tai_trong_toi_da:
            return float('inf'), float('inf'), False # Infeasible

        # 2. Duyệt từng điểm để tính Time Window và Chi phí
        for kh_idx in lo_trinh:
            kh = self.khach_hang[kh_idx]
            curr_idx = kh_idx + 1 # Chuyển sang index ma trận OD (Kho=0)
            
            # Quãng đường đi từ điểm trước đến điểm hiện tại
            tg_di_duong = self.ma_tran_thoi_gian[vi_tri_truoc][curr_idx]
            
            # Bước A: Tính thời gian đến nơi
            thoi_gian_den_noi = thoi_gian_hien_tai + tg_di_duong
            
            # Bước B: Check Muộn (Late) -> Phạt nặng
            if thoi_gian_den_noi > kh['thoi_gian_dong_cua']:
                return float('inf'), float('inf'), False # Infeasible
            
            # Bước C: Check Sớm (Early) -> Bắt buộc chờ
            if thoi_gian_den_noi < kh['thoi_gian_mo_cua']:
                thoi_gian_cho = kh['thoi_gian_mo_cua'] - thoi_gian_den_noi
                # Cộng chi phí lương tài xế trong lúc chờ
                tong_chi_phi += thoi_gian_cho * self.luong_tai_xe_phut
                thoi_gian_den_noi = kh['thoi_gian_mo_cua']
                
            # Bước D: Đi tiếp sau khi bốc dỡ
            thoi_gian_hien_tai = thoi_gian_den_noi + kh['thoi_gian_boc_do']
            
            # Cộng chi phí di chuyển và khí thải
            tong_chi_phi += self.ma_tran_chi_phi[vi_tri_truoc][curr_idx]
            tong_khi_thai += self.ma_tran_khi_thai[vi_tri_truoc][curr_idx]
            
            vi_tri_truoc = curr_idx

        # Quay về kho
        tong_chi_phi += self.ma_tran_chi_phi[vi_tri_truoc][0]
        tong_khi_thai += self.ma_tran_khi_thai[vi_tri_truoc][0]
        
        return tong_chi_phi, tong_khi_thai, True

    def _tinh_tong_global(self, solution: List[List[int]]) -> Tuple[float, float, float, bool]:
        """Tính hàm mục tiêu tổng cho cả đội xe 17 chiếc."""
        global_cp = 0.0
        global_kt = 0.0
        for r in solution:
            cp, kt, ok = self._danh_gia_mot_xe(r)
            if not ok: return float('inf'), 0, 0, False
            global_cp += cp
            global_kt += kt
        
        f = self.alpha * global_cp + self.beta * global_kt
        return f, global_cp, global_kt, True

    # -------------------------------------------------------------------------
    # CÁC TOÁN TỬ TABU SEARCH (Inter-route)
    # -------------------------------------------------------------------------
    def toan_tu_rut_cam(self, s: List[List[int]]) -> List[List[int]]:
        """Rút khách hàng từ xe A cắm sang xe B."""
        new_s = copy.deepcopy(s)
        avail_xe = [i for i, r in enumerate(new_s) if r]
        if len(avail_xe) < 1: return new_s
        
        xe_a = random.choice(avail_xe)
        xe_b = random.choice(range(self.so_xe))
        
        kh_idx = new_s[xe_a].pop(random.randrange(len(new_s[xe_a])))
        ins_pos = random.randint(0, len(new_s[xe_b]))
        new_s[xe_b].insert(ins_pos, kh_idx)
        return new_s

    def toan_tu_doi_cheo(self, s: List[List[int]]) -> List[List[int]]:
        """Hoán đổi 2 khách hàng giữa 2 lộ trình xe khác nhau."""
        new_s = copy.deepcopy(s)
        avail_xe = [i for i, r in enumerate(new_s) if r]
        if len(avail_xe) < 2: return new_s
        
        xe_a, xe_b = random.sample(avail_xe, 2)
        idx_a = random.randrange(len(new_s[xe_a]))
        idx_b = random.randrange(len(new_s[xe_b]))
        
        new_s[xe_a][idx_a], new_s[xe_b][idx_b] = new_s[xe_b][idx_b], new_s[xe_a][idx_a]
        return new_s

    # -------------------------------------------------------------------------
    # VÒNG LẶP CHÍNH
    # -------------------------------------------------------------------------
    def giai(self) -> Dict:
        in_tieu_de("LOP 3: TABU SEARCH (Refactored Modular)")
        
        # 1. Khởi tạo đội xe 17 chiếc rỗng
        solution = [[] for _ in range(self.so_xe)]
        kh_cho_giao = list(range(self.so_khach_hang))
        random.shuffle(kh_cho_giao)
        
        # Chia khách vào xe (Khởi tạo đơn giản)
        for i, kh in enumerate(kh_cho_giao):
            solution[i % self.so_xe].append(kh)
            
        f_best, cp_best, kt_best, _ = self._tinh_tong_global(solution)
        self.lo_trinh_tot_nhat = copy.deepcopy(solution)
        self.f_tot_nhat = f_best

        # 2. Lặp Tabu
        for vong_lap in range(self.toi_da_vong_lap):
            tap_lan_can = []
            for _ in range(40):
                if random.random() < 0.6:
                    tap_lan_can.append(self.toan_tu_rut_cam(solution))
                else:
                    tap_lan_can.append(self.toan_tu_doi_cheo(solution))
            
            best_lc = None
            f_best_lc = float('inf')
            
            for lc in tap_lan_can:
                f, cp, kt, ok = self._tinh_tong_global(lc)
                sol_str = str(lc)
                if ok and sol_str not in self.tabu_list:
                    if f < f_best_lc:
                        f_best_lc = f
                        best_lc = lc
            
            if best_lc:
                solution = best_lc
                self.tabu_list.append(str(best_lc))
                if len(self.tabu_list) > self.do_dai_tabu:
                    self.tabu_list.pop(0)
                
                if f_best_lc < self.f_tot_nhat:
                    self.f_tot_nhat = f_best_lc
                    self.lo_trinh_tot_nhat = copy.deepcopy(best_lc)
                    in_thong_bao(f"  Vong {vong_lap}: Tim thay ky luc moi F = {self.f_tot_nhat:.4f}")

            if vong_lap % 20 == 0:
                in_tien_trinh(vong_lap/self.toi_da_vong_lap*100, f"Giai Tabu ({vong_lap}/{self.toi_da_vong_lap})")

        return self._xuat_ket_qua()

    def _xuat_ket_qua(self) -> Dict:
        f, cp, kt, _ = self._tinh_tong_global(self.lo_trinh_tot_nhat)
        res = {
            "ham_muc_tieu": f,
            "tong_chi_phi": cp,
            "tong_khi_thai": kt,
            "lo_trinh": {}
        }
        for i, r in enumerate(self.lo_trinh_tot_nhat):
            if not r: continue
            ten_kh = [self.khach_hang[k]['ten'] for k in r]
            res["lo_trinh"][f"Xe_{i+1:02d}"] = {
                "mo_ta": " -> ".join(["[Kho]"] + ten_kh + ["[Kho]"]),
                "thu_tu": r
            }
        in_ket_qua(f"\nDONE - Global Cost: ${cp:.2f} | Emissions: {kt:.2f}g")
        return res
