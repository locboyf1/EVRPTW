"""
=============================================================
LỚP 3: VRP SOLVER ENGINE — TABU SEARCH (REFACTORED)
Dựa trên phương pháp luận: Wygonik & Goodchild (2010)
Nhiệm vụ: Giải bài toán VRPTW Đa mục tiêu với đội xe 17 chiếc.
Ràng buộc: Tải trọng (90 đơn vị) và Cửa sổ thời gian (Time Windows).
=============================================================
"""

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
    Bộ giải Tabu Search hỗ trợ đa tuyến (Multi-route), 
    phù hợp cho đội xe 17 chiếc của Wygonik & Goodchild.
    """

    def __init__(self,
                 so_xe: int = 17,
                 tai_trong_toi_da: float = 90.0,
                 danh_sach_khach_hang: list = [],
                 ma_tran_chi_phi: np.ndarray = None,
                 ma_tran_khi_thai: np.ndarray = None,
                 ma_tran_thoi_gian_giay: np.ndarray = None,
                 toi_da_vong_lap: int = 300,
                 do_dai_tabu: int = 15,
                 trong_so_chi_phi: float = 0.5,
                 trong_so_khi_thai: float = 0.5):
        
        self.so_xe = so_xe
        self.tai_trong_toi_da = tai_trong_toi_da
        self.khach_hang = danh_sach_khach_hang
        self.so_khach_hang = len(danh_sach_khach_hang)
        
        # Ma trận OD (Dữ liệu tĩnh từ Lớp 2)
        self.ma_tran_chi_phi = ma_tran_chi_phi
        self.ma_tran_khi_thai = ma_tran_khi_thai
        self.ma_tran_thoi_gian_giay = ma_tran_thoi_gian_giay
        
        # Tham số thuật toán
        self.toi_da_vong_lap = toi_da_vong_lap
        self.do_dai_tabu = do_dai_tabu
        self.alpha = trong_so_chi_phi
        self.beta = trong_so_khi_thai
        
        # Tabu List lưu các lộ trình đã đi qua để tránh lặp (chuỗi hóa kết quả)
        self.tabu_list: List[str] = []
        
        # Kết quả tốt nhất toàn cục
        self.lo_trinh_tot_nhat = None
        self.f_tot_nhat = float('inf')

    # -------------------------------------------------------------------------
    # BƯỚC 1: KHỞI TẠO LỘ TRÌNH (Phân bổ đơn giản)
    # -------------------------------------------------------------------------
    def _khoi_tao_lo_trinh_ban_dau(self) -> List[List[int]]:
        """
        Khởi tạo 17 mảng con rỗng và phân bổ khách hàng ngẫu nhiên.
        """
        solution = [[] for _ in range(self.so_xe)]
        tat_ca_kh = list(range(self.so_khach_hang))
        random.shuffle(tat_ca_kh)
        
        # Chia đều khách hàng cho các xe
        for i, kh_idx in enumerate(tat_ca_kh):
            solution[i % self.so_xe].append(kh_idx)
            
        return solution

    # -------------------------------------------------------------------------
    # BƯỚC 2: ĐÁNH GIÁ (Kiểm tra Tải trọng + Time Window)
    # -------------------------------------------------------------------------
    def _danh_gia_mot_xe(self, lo_trinh_xe: List[int]) -> Tuple[float, float, bool]:
        """
        Kiểm tra tính hợp lệ và tính toán chi phí cho 1 xe duy nhất.
        """
        if not lo_trinh_xe: return 0.0, 0.0, True
        
        tong_tai_trong = 0.0
        tong_chi_phi = 0.0
        tong_khi_thai = 0.0
        thoi_gian_hien_tai = 0.0 # đơn vị: phút
        vi_tri_truoc = 0 # 0 là Kho

        for kh_idx in lo_trinh_xe:
            kh = self.khach_hang[kh_idx]
            idx_mat_tran = kh_idx + 1 # dịch index vì ma trận có Kho ở vị trí 0
            
            # 1. Kiểm tra tải trọng
            tong_tai_trong += kh.get('nhu_cau', 0)
            if tong_tai_trong > self.tai_trong_toi_da:
                return float('inf'), float('inf'), False
            
            # 2. Tính thời gian và kiểm tra Time Window
            # Cộng thời gian di chuyển từ điểm trước đến điểm hiện tại
            tg_di_chuyen = self.ma_tran_thoi_gian_giay[vi_tri_truoc][idx_mat_tran] / 60.0
            thoi_gian_hien_tai += tg_di_chuyen
            
            # Nếu đến trước giờ mở cửa -> phải chờ
            if thoi_gian_hien_tai < kh['thoi_gian_mo_cua']:
                thoi_gian_hien_tai = kh['thoi_gian_mo_cua']
            
            # Nếu đến sau giờ đóng cửa -> Vi phạm
            if thoi_gian_hien_tai > kh['thoi_gian_dong_cua']:
                return float('inf'), float('inf'), False
            
            # Sau khi phục vụ xong, cộng thêm thời gian bốc xếp hàng
            thoi_gian_hien_tai += kh['thoi_gian_boc_do']
            
            # 3. Cộng dồn chi phi & khí thải từ ma trận
            tong_chi_phi += self.ma_tran_chi_phi[vi_tri_truoc][idx_mat_tran]
            tong_khi_thai += self.ma_tran_khi_thai[vi_tri_truoc][idx_mat_tran]
            
            vi_tri_truoc = idx_mat_tran

        # Cộng chi phí quay về kho
        tong_chi_phi += self.ma_tran_chi_phi[vi_tri_truoc][0]
        tong_khi_thai += self.ma_tran_khi_thai[vi_tri_truoc][0]
        
        return tong_chi_phi, tong_khi_thai, True

    def _tinh_tong_ham_muc_tieu(self, solution: List[List[int]]) -> Tuple[float, float, float, bool]:
        """
        Tính tổng F = alpha * ChiPhi + beta * KhiThai cho cả đội xe 17 chiếc.
        """
        tong_cp = 0.0
        tong_kt = 0.0
        for lo_trinh in solution:
            cp, kt, hop_le = self._danh_gia_mot_xe(lo_trinh)
            if not hop_le: return float('inf'), 0, 0, False
            tong_cp += cp
            tong_kt += kt
            
        f_value = self.alpha * tong_cp + self.beta * tong_kt
        return f_value, tong_cp, tong_kt, True

    # -------------------------------------------------------------------------
    # BƯỚC 3: CÁC TOÁN TỬ LÂN CẬN (INTER-ROUTE)
    # -------------------------------------------------------------------------
    def _sinh_hang_xom(self, hien_tai: List[List[int]]) -> List[List[List[int]]]:
        """
        Sinh tập lân cận bằng các phép toán Relocate và Exchange giữa các xe.
        """
        hang_xom = []
        
        # Toản tử 1: Relocate (Rút từ xe A cắm vào xe B)
        # Chúng ta thử nghiệm 50 biến thể ngẫu nhiên để tối ưu tốc độ
        for _ in range(50): 
            xe_a, xe_b = random.sample(range(self.so_xe), 2)
            if not hien_tai[xe_a]: continue
            
            moi = copy.deepcopy(hien_tai)
            kh_idx = moi[xe_a].pop(random.randrange(len(moi[xe_a])))
            insert_pos = random.randint(0, len(moi[xe_b]))
            moi[xe_b].insert(insert_pos, kh_idx)
            hang_xom.append(moi)

        # Toán tử 2: Exchange (Tráo đổi khách giữa 2 xe)
        for _ in range(50):
            xe_a, xe_b = random.sample(range(self.so_xe), 2)
            if not hien_tai[xe_a] or not hien_tai[xe_b]: continue
            
            moi = copy.deepcopy(hien_tai)
            idx_a = random.randrange(len(moi[xe_a]))
            idx_b = random.randrange(len(moi[xe_b]))
            moi[xe_a][idx_a], moi[xe_b][idx_b] = moi[xe_b][idx_b], moi[xe_a][idx_a]
            hang_xom.append(moi)
            
        return hang_xom

    # -------------------------------------------------------------------------
    # BƯỚC 4: VÒNG LẶP CHÍNH CỦA TABU SEARCH
    # -------------------------------------------------------------------------
    def giai(self) -> Dict:
        in_tieu_de("LỚP 3: VRP SOLVER (Refactored: Wygonik & Goodchild 2010)")
        in_thong_bao(f"Đội xe cố định: {self.so_xe} chiếc | Tải trọng tối đa: {self.tai_trong_toi_da} đơn vị")
        
        # 1. Khởi tạo lộ trình ban đầu
        lo_trinh_hien_tai = self._khoi_tao_lo_trinh_ban_dau()
        f_hien_tai, cp_hien_tai, kt_hien_tai, _ = self._tinh_tong_ham_muc_tieu(lo_trinh_hien_tai)
        
        self.lo_trinh_tot_nhat = copy.deepcopy(lo_trinh_hien_tai)
        self.f_tot_nhat = f_hien_tai
        
        # 2. Vòng lặp tối ưu hóa
        for i in range(self.toi_da_vong_lap):
            tap_hang_xom = self._sinh_hang_xom(lo_trinh_hien_tai)
            
            tot_nhat_hang_xom = None
            f_tot_nhat_hang_xom = float('inf')
            
            for nx in tap_hang_xom:
                f_nx, cp_nx, kt_nx, hop_le = self._tinh_tong_ham_muc_tieu(nx)
                
                # Biến lộ trình thành chuỗi để kiểm tra Tabu List
                solution_str = str(nx)
                
                if hop_le and solution_str not in self.tabu_list:
                    if f_nx < f_tot_nhat_hang_xom:
                        f_tot_nhat_hang_xom = f_nx
                        tot_nhat_hang_xom = nx
                        
            # Cập nhật trạng thái nếu tìm thấy nước đi tốt hơn không bị cấm
            if tot_nhat_hang_xom:
                lo_trinh_hien_tai = tot_nhat_hang_xom
                f_hien_tai = f_tot_nhat_hang_xom
                
                # Thêm vào Tabu List (FIFO)
                self.tabu_list.append(str(tot_nhat_hang_xom))
                if len(self.tabu_list) > self.do_dai_tabu:
                    self.tabu_list.pop(0)
                    
                # Ghi nhận nếu đây là lời giải tốt nhất từ trước tới nay
                if f_hien_tai < self.f_tot_nhat:
                    self.f_tot_nhat = f_hien_tai
                    self.lo_trinh_tot_nhat = copy.deepcopy(lo_trinh_hien_tai)
                    in_thong_bao(f" ✨ Vòng {i:3d}: Tìm thấy kỷ lục mới F = {self.f_tot_nhat:.4f}")

            # Cập nhật thanh tiến trình
            if i % max(1, self.toi_da_vong_lap // 10) == 0:
                in_tien_trinh(i/self.toi_da_vong_lap*100, f"Đang giải VRP (Vòng {i}/{self.toi_da_vong_lap})")

        return self._dong_goi_ket_qua()

    def _dong_goi_ket_qua(self) -> Dict:
        """Đóng gói và hiển thị tổng kết kết quả."""
        f_val, cp_val, kt_val, _ = self._tinh_tong_ham_muc_tieu(self.lo_trinh_tot_nhat)
        
        res = {
            "ham_muc_tieu": f_val,
            "tong_chi_phi": cp_val,
            "tong_khi_thai": kt_val,
            "lo_trinh": {}
        }
        
        in_ket_qua("\n═══════════════════════════════════════")
        in_ket_qua("     KẾT QUẢ ĐỘI XE 17 CHIẾC")
        in_ket_qua("═══════════════════════════════════════")
        
        for idx, route in enumerate(self.lo_trinh_tot_nhat):
            if not route: continue
            ten_xe = f"Xe_{idx+1:02d}"
            ten_cac_kh = [self.khach_hang[k]['ten'] for k in route]
            res["lo_trinh"][ten_xe] = {
                "mo_ta": " -> ".join(["[Kho]"] + ten_cac_kh + ["[Kho]"]),
                "thu_tu": route
            }
            in_ket_qua(f"  [{ten_xe}]: {res['lo_trinh'][ten_xe]['mo_ta']}")
            
        in_ket_qua(f"\n✅ TỔNG KẾT: CP = ${cp_val:.2f} | KT = {kt_val:.2f}g")
        return res
