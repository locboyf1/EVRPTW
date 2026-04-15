"""
=============================================================
LỚP 3: VRP SOLVER ENGINE — TABU SEARCH
Nhiệm vụ: Giải bài toán VRP multi-objective bằng Tabu Search
          tự xây dựng từ đầu, KHÔNG dùng OR-Tools hay bất kỳ
          thư viện giải VRP nào.

NGUYÊN TẮC BẤT BIẾN:
  - Tabu Search CHỈ tra cứu 2 Ma trận OD tĩnh từ Lớp 2.
  - Tabu Search KHÔNG BAO GIỜ gọi đồ thị OSMnx hay Dijkstra.
  - Đây là mô phỏng chính xác cơ chế của ArcGIS VRP Solver.

CẤU TRÚC GIẢI THUẬT:
  ┌──────────────────────────────────────────────────┐
  │  1. Khởi tạo lộ trình ban đầu (Nearest Neighbor) │
  │  2. Vòng lặp Tabu Search (toi_da_vong_lap lần):  │
  │     a. Sinh tập hàng xóm (Relocate + Exchange)   │
  │     b. Đánh giá mỗi nước đi (tra ma trận OD)     │
  │     c. Kiểm tra Time Window (biến cộng dồn)      │
  │     d. Chọn nước đi tốt nhất không trong Tabu    │
  │     e. Cập nhật Tabu List (FIFO)                 │
  │     f. Cập nhật lời giải tốt nhất toàn cục       │
  └──────────────────────────────────────────────────┘
=============================================================
"""

import sys
import os
import copy
import random
from typing import List, Tuple, Dict, Optional

# Thêm đường dẫn gốc vào sys.path
_THU_MUC_GOC = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _THU_MUC_GOC not in sys.path:
    sys.path.insert(0, _THU_MUC_GOC)

import numpy as np
from giao_dien.terminal_ui import (
    in_tieu_de, in_thong_bao, in_canh_bao, in_tien_trinh, in_ket_qua
)


class TabuSearchVRPSolver:
    """
    Tabu Search giải bài toán VRPTW (VRP + Time Windows) đa mục tiêu.
    Hoàn toàn tự xây dựng — không phụ thuộc thư viện VRP bên ngoài.

    NGUỒN DỮ LIỆU DUY NHẤT: 2 Ma trận OD từ Lớp 2.
    """

    def __init__(self,
                 so_xe: int,
                 danh_sach_khach_hang: list,
                 cau_hinh_xe: list,
                 # ─── 2 Ma trận OD tĩnh từ Lớp 2 ───
                 ma_tran_chi_phi: np.ndarray,
                 ma_tran_khi_thai: np.ndarray,       # Đã nhân hệ số loại xe
                 ma_tran_thoi_gian_giay: np.ndarray,
                 # ─── Tham số Tabu Search ───
                 toi_da_vong_lap: int = 300,
                 do_dai_tabu: int = 12,
                 trong_so_chi_phi: float = 0.5,      # α
                 trong_so_khi_thai: float = 0.5      # β
                 ):
        """
        Khởi tạo bộ giải.

        Lưu ý về index:
            - Ma trận OD: index 0 = kho, index 1..N-1 = khách hàng
            - danh_sach_khach_hang: index 0-based (không chứa kho)
            - Khi tra ma trận cho KH[k]: dùng index k+1
        """
        self.so_xe             = so_xe
        self.khach_hang        = danh_sach_khach_hang
        self.so_khach_hang     = len(danh_sach_khach_hang)
        self.cau_hinh_xe       = cau_hinh_xe

        # ─── Lưu trữ 2 Ma trận OD (nguồn dữ liệu duy nhất) ───
        self.ma_tran_chi_phi         = ma_tran_chi_phi
        self.ma_tran_khi_thai        = ma_tran_khi_thai
        self.ma_tran_thoi_gian_giay  = ma_tran_thoi_gian_giay

        # ─── Tham số Tabu ───
        self.toi_da_vong_lap   = toi_da_vong_lap
        self.do_dai_tabu       = do_dai_tabu
        self.trong_so_chi_phi  = trong_so_chi_phi
        self.trong_so_khi_thai = trong_so_khi_thai

        # ─── Tabu List: mảng FIFO lưu các nước đi đã thực hiện ───
        self.tabu_list: List[tuple] = []

        # ─── Lời giải tốt nhất toàn cục ───
        self.lo_trinh_tot_nhat:        Optional[List[List[int]]] = None
        self.ham_muc_tieu_tot_nhat:    float = float("inf")
        self.chi_phi_tot_nhat:         float = float("inf")
        self.khi_thai_tot_nhat:        float = float("inf")

    # ═══════════════════════════════════════════════════════════
    # BƯỚC 1: KHỞI TẠO LỘ TRÌNH (NEAREST NEIGHBOR HEURISTIC)
    # ═══════════════════════════════════════════════════════════
    def _khoi_tao_lo_trinh_nearest_neighbor(self) -> List[List[int]]:
        """
        Xây dựng lộ trình ban đầu bằng heuristic Nearest Neighbor.
        Phân công khách hàng cho từng xe luân phiên, mỗi lần chọn KH gần nhất.

        Index trong lộ trình: 0-based (index của self.khach_hang).
        Index trong ma trận:  index_kh + 1 (vì kho chiếm index 0).
        """
        # Danh sách KH chưa được phân công (index 0-based của self.khach_hang)
        khach_chua_phan_cong = list(range(self.so_khach_hang))
        random.shuffle(khach_chua_phan_cong)

        lo_trinh = [[] for _ in range(self.so_xe)]
        xe_hien_tai = 0
        vi_tri_hien_tai_mat_tran = 0  # Bắt đầu từ kho (index 0 trong ma trận)

        while khach_chua_phan_cong:
            # Tìm KH chưa được phân công có thời gian đi ít nhất từ vị trí hiện tại
            kh_gan_nhat_idx      = None
            thoi_gian_ngan_nhat  = float("inf")

            for kh_idx in khach_chua_phan_cong:
                idx_mat_tran = kh_idx + 1  # +1 vì kho chiếm index 0 trong ma trận
                tg = self.ma_tran_thoi_gian_giay[vi_tri_hien_tai_mat_tran][idx_mat_tran]
                if tg < thoi_gian_ngan_nhat:
                    thoi_gian_ngan_nhat  = tg
                    kh_gan_nhat_idx      = kh_idx

            # Phân công KH gần nhất cho xe hiện tại
            lo_trinh[xe_hien_tai].append(kh_gan_nhat_idx)
            khach_chua_phan_cong.remove(kh_gan_nhat_idx)
            vi_tri_hien_tai_mat_tran = kh_gan_nhat_idx + 1

            # Chuyển sang xe tiếp theo theo vòng tròn
            xe_hien_tai = (xe_hien_tai + 1) % self.so_xe
            if xe_hien_tai == 0:
                vi_tri_hien_tai_mat_tran = 0  # Reset về kho

        return lo_trinh

    # ═══════════════════════════════════════════════════════════
    # BƯỚC 2A: ĐÁNH GIÁ MỘT XE — KIỂM TRA TIME WINDOW (CỨNG)
    # ═══════════════════════════════════════════════════════════
    def _danh_gia_mot_xe(self, lo_trinh_mot_xe: List[int]) -> Tuple[float, float, bool]:
        """
        Tính chi phí + khí thải cho MỘT xe, đồng thời kiểm tra Time Window cứng.
        CHỈ TRA CỨU TỪ MA TRẬN OD — không gọi đồ thị, không gọi Dijkstra.

        BIẾN CỐT LÕI: thoi_gian_hien_tai (phút từ đầu ca)
        CÔNG THỨC CỘNG DỒN tại điểm k:
          thoi_gian_hien_tai += di_duong_phut       (tra ma trận)
          IF thoi_gian_hien_tai < mo_cua → chờ
          IF thoi_gian_hien_tai > dong_cua → INFEASIBLE, trả về (∞, ∞, False)
          thoi_gian_hien_tai += thoi_gian_boc_do

        Trả về:
            (chi_phi_usd, khi_thai_gram, la_hop_le)
        """
        if not lo_trinh_mot_xe:
            return 0.0, 0.0, True

        tong_chi_phi  = 0.0
        tong_khi_thai = 0.0

        vi_tri_truoc_mat_tran = 0       # Bắt đầu từ kho
        thoi_gian_hien_tai    = 0.0     # Phút

        for kh_idx in lo_trinh_mot_xe:
            idx_mat_tran = kh_idx + 1   # Chuyển sang index ma trận
            khach = self.khach_hang[kh_idx]

            # ── Tra ma trận: thời gian đi đường ──
            tg_di_duong_giay = self.ma_tran_thoi_gian_giay[vi_tri_truoc_mat_tran][idx_mat_tran]
            tg_di_duong_phut = tg_di_duong_giay / 60.0

            # ── Tra ma trận: chi phí và khí thải ──
            chi_phi  = self.ma_tran_chi_phi[vi_tri_truoc_mat_tran][idx_mat_tran]
            khi_thai = self.ma_tran_khi_thai[vi_tri_truoc_mat_tran][idx_mat_tran]

            # Đường đi vô cực → infeasible
            if chi_phi >= 1e8 or khi_thai >= 1e8:
                return float("inf"), float("inf"), False

            tong_chi_phi  += chi_phi
            tong_khi_thai += khi_thai

            # ── Cộng dồn thời gian ──
            thoi_gian_hien_tai += tg_di_duong_phut

            # ── Kiểm tra Time Window cứng ──
            tg_mo_cua  = khach["thoi_gian_mo_cua"]
            tg_dong_cua = khach["thoi_gian_dong_cua"]
            tg_boc_do  = khach["thoi_gian_boc_do"]

            # Đến sớm → chờ cửa mở
            if thoi_gian_hien_tai < tg_mo_cua:
                thoi_gian_hien_tai = tg_mo_cua

            # Đến muộn → vi phạm time window → INFEASIBLE
            if thoi_gian_hien_tai > tg_dong_cua:
                return float("inf"), float("inf"), False

            # Cộng thêm thời gian bốc/dỡ hàng
            thoi_gian_hien_tai += tg_boc_do

            vi_tri_truoc_mat_tran = idx_mat_tran

        # ── Thêm chi phí đoạn về kho ──
        chi_phi_ve_kho  = self.ma_tran_chi_phi[vi_tri_truoc_mat_tran][0]
        khi_thai_ve_kho = self.ma_tran_khi_thai[vi_tri_truoc_mat_tran][0]
        tong_chi_phi  += chi_phi_ve_kho
        tong_khi_thai += khi_thai_ve_kho

        return tong_chi_phi, tong_khi_thai, True

    # ═══════════════════════════════════════════════════════════
    # BƯỚC 2B: HÀM MỤC TIÊU — ĐÁNH GIÁ TOÀN ĐỘI XE
    # ═══════════════════════════════════════════════════════════
    def _ham_muc_tieu(self, lo_trinh: List[List[int]]) -> Tuple[float, float, float, bool]:
        """
        Tính tổng hàm mục tiêu đa mục tiêu cho TOÀN ĐỘI XE.
        Dùng để so sánh giữa các vòng lặp Tabu Search.

        Công thức:
            F = α × Chi_phí_tổng + β × Khí_thải_tổng

        Trả về:
            (ham_muc_tieu, tong_chi_phi, tong_khi_thai, la_hop_le)
        """
        tong_chi_phi  = 0.0
        tong_khi_thai = 0.0

        for lo_trinh_mot_xe in lo_trinh:
            cp, kt, hop_le = self._danh_gia_mot_xe(lo_trinh_mot_xe)
            if not hop_le:
                return float("inf"), float("inf"), float("inf"), False
            tong_chi_phi  += cp
            tong_khi_thai += kt

        ham_muc_tieu = (self.trong_so_chi_phi * tong_chi_phi +
                        self.trong_so_khi_thai * tong_khi_thai)

        return ham_muc_tieu, tong_chi_phi, tong_khi_thai, True

    # ═══════════════════════════════════════════════════════════
    # BƯỚC 3A: INTER-ROUTE MOVE — RELOCATE
    # Rút khách hàng từ Xe_nguon, cắm vào vị trí khác của Xe_dich
    # ═══════════════════════════════════════════════════════════
    def _sinh_nuoc_di_relocate(self,
                                lo_trinh: List[List[int]]
                                ) -> List[Tuple]:
        """
        Sinh danh sách tất cả nước đi Relocate.

        RELOCATE: Rút KH[xe_nguon][vt_nguon] → Chèn vào xe_dich tại vt_dich.

        Trả về list[tuple]:
            ((loai, xe_nguon, vt_nguon, xe_dich, vt_dich), lo_trinh_sau_nuoc_di)
        """
        tat_ca_nuoc_di = []

        for xe_nguon in range(self.so_xe):
            if not lo_trinh[xe_nguon]:
                continue

            for vt_nguon, kh_chuyen in enumerate(lo_trinh[xe_nguon]):
                for xe_dich in range(self.so_xe):
                    if xe_nguon == xe_dich:
                        continue  # Không relocate trong cùng một xe

                    for vt_dich in range(len(lo_trinh[xe_dich]) + 1):
                        # Tạo bản sao lộ trình và thực hiện nước đi
                        lo_trinh_moi = copy.deepcopy(lo_trinh)
                        lo_trinh_moi[xe_nguon].pop(vt_nguon)
                        lo_trinh_moi[xe_dich].insert(vt_dich, kh_chuyen)

                        nuoc_di = ("relocate", xe_nguon, vt_nguon, xe_dich, vt_dich)
                        tat_ca_nuoc_di.append((nuoc_di, lo_trinh_moi))

        return tat_ca_nuoc_di

    # ═══════════════════════════════════════════════════════════
    # BƯỚC 3B: INTER-ROUTE MOVE — EXCHANGE
    # Đổi chéo 2 khách hàng giữa 2 xe khác nhau
    # ═══════════════════════════════════════════════════════════
    def _sinh_nuoc_di_exchange(self,
                                lo_trinh: List[List[int]]
                                ) -> List[Tuple]:
        """
        Sinh danh sách tất cả nước đi Exchange.

        EXCHANGE: Đổi vị trí KH[xe_1][vt_1] ↔ KH[xe_2][vt_2] (khác xe).
        Chỉ xét cặp xe (xe_1 < xe_2) để tránh cặp trùng lặp.

        Trả về list[tuple]:
            ((loai, xe_1, vt_1, xe_2, vt_2), lo_trinh_sau_nuoc_di)
        """
        tat_ca_nuoc_di = []

        for xe_1 in range(self.so_xe):
            if not lo_trinh[xe_1]:
                continue

            for xe_2 in range(xe_1 + 1, self.so_xe):
                if not lo_trinh[xe_2]:
                    continue

                for vt_1, kh_1 in enumerate(lo_trinh[xe_1]):
                    for vt_2, kh_2 in enumerate(lo_trinh[xe_2]):
                        lo_trinh_moi = copy.deepcopy(lo_trinh)
                        # Đổi chéo hai khách hàng
                        lo_trinh_moi[xe_1][vt_1] = kh_2
                        lo_trinh_moi[xe_2][vt_2] = kh_1

                        nuoc_di = ("exchange", xe_1, vt_1, xe_2, vt_2)
                        tat_ca_nuoc_di.append((nuoc_di, lo_trinh_moi))

        return tat_ca_nuoc_di

    # ═══════════════════════════════════════════════════════════
    # BƯỚC 4: KIỂM TRA VÀ CẬP NHẬT TABU LIST
    # ═══════════════════════════════════════════════════════════
    def _la_tabu(self, nuoc_di: tuple) -> bool:
        """Kiểm tra nước đi có trong Tabu List không."""
        return nuoc_di in self.tabu_list

    def _them_vao_tabu(self, nuoc_di: tuple):
        """
        Thêm nước đi vào cuối Tabu List.
        Nếu vượt độ dài tối đa → xóa phần tử đầu (FIFO — First In First Out).
        """
        self.tabu_list.append(nuoc_di)
        if len(self.tabu_list) > self.do_dai_tabu:
            self.tabu_list.pop(0)

    # ═══════════════════════════════════════════════════════════
    # VÒNG LẶP CHÍNH: TABU SEARCH
    # ═══════════════════════════════════════════════════════════
    def giai(self) -> Dict:
        """
        Hàm chính: Khởi động Tabu Search và trả về lời giải tốt nhất.

        Quy trình:
          1. Khởi tạo lộ trình ban đầu (Nearest Neighbor)
          2. Lặp toi_da_vong_lap lần:
             a. Sinh hàng xóm = Relocate ∪ Exchange
             b. Đánh giá từng ứng viên (tra ma trận OD + kiểm tra TW)
             c. Chọn ứng viên tốt nhất không bị Tabu (hoặc vượt Aspiration)
             d. Cập nhật Tabu List (thêm nước đi đã chọn)
             e. Cập nhật best solution nếu tốt hơn
          3. Trả về kết quả tốt nhất tìm được
        """
        in_tieu_de("LỚP 3: VRP SOLVER — TABU SEARCH")
        in_thong_bao(f"Số khách hàng:       {self.so_khach_hang}")
        in_thong_bao(f"Số xe:               {self.so_xe}")
        in_thong_bao(f"Số vòng lặp tối đa:  {self.toi_da_vong_lap}")
        in_thong_bao(f"Độ dài Tabu List:    {self.do_dai_tabu}")
        in_thong_bao(f"α (chi phí): {self.trong_so_chi_phi} | "
                     f"β (khí thải): {self.trong_so_khi_thai}")

        # ── Bước 1: Khởi tạo ──
        lo_trinh_hien_tai = self._khoi_tao_lo_trinh_nearest_neighbor()
        f0, cp0, kt0, _ = self._ham_muc_tieu(lo_trinh_hien_tai)

        self.lo_trinh_tot_nhat     = copy.deepcopy(lo_trinh_hien_tai)
        self.ham_muc_tieu_tot_nhat = f0
        self.chi_phi_tot_nhat      = cp0
        self.khi_thai_tot_nhat     = kt0

        in_thong_bao(
            f"Lộ trình khởi tạo — F={f0:.4f} "
            f"(CP=${cp0:.2f}, KT={kt0:.1f}g CO2)"
        )

        # ── Bước 2: Vòng lặp Tabu Search ──
        for vong_lap in range(self.toi_da_vong_lap):

            # a. Sinh hàng xóm
            tat_ca_nuoc_di = (
                self._sinh_nuoc_di_relocate(lo_trinh_hien_tai) +
                self._sinh_nuoc_di_exchange(lo_trinh_hien_tai)
            )

            if not tat_ca_nuoc_di:
                in_canh_bao(f"Không còn nước đi hợp lệ tại vòng {vong_lap}. Dừng.")
                break

            # b. Đánh giá và chọn nước đi tốt nhất thỏa điều kiện
            nuoc_di_chon  = None
            lo_trinh_chon = None
            f_chon        = float("inf")
            cp_chon       = float("inf")
            kt_chon       = float("inf")

            for nuoc_di, lo_trinh_ung_vien in tat_ca_nuoc_di:
                f_uv, cp_uv, kt_uv, hop_le = self._ham_muc_tieu(lo_trinh_ung_vien)

                if not hop_le:
                    continue  # Bỏ qua lộ trình vi phạm time window

                # c. Điều kiện chấp nhận:
                #    - Không trong Tabu List, HOẶC
                #    - Trong Tabu nhưng tốt hơn best toàn cục (Aspiration Criterion)
                la_tabu             = self._la_tabu(nuoc_di)
                thoa_aspiration     = f_uv < self.ham_muc_tieu_tot_nhat

                if (not la_tabu or thoa_aspiration) and f_uv < f_chon:
                    nuoc_di_chon  = nuoc_di
                    lo_trinh_chon = lo_trinh_ung_vien
                    f_chon        = f_uv
                    cp_chon       = cp_uv
                    kt_chon       = kt_uv

            if nuoc_di_chon is None:
                # Tất cả nước đi đều bị Tabu và không thỏa Aspiration
                continue

            # d. Cập nhật trạng thái hiện tại
            lo_trinh_hien_tai = lo_trinh_chon

            # d. Thêm nước đi vào Tabu List
            self._them_vao_tabu(nuoc_di_chon)

            # e. Cập nhật lời giải tốt nhất
            if f_chon < self.ham_muc_tieu_tot_nhat:
                self.lo_trinh_tot_nhat     = copy.deepcopy(lo_trinh_chon)
                self.ham_muc_tieu_tot_nhat = f_chon
                self.chi_phi_tot_nhat      = cp_chon
                self.khi_thai_tot_nhat     = kt_chon
                in_thong_bao(
                    f"  ✨ Vòng {vong_lap:4d}: Cải thiện! "
                    f"F={f_chon:.4f} | CP=${cp_chon:.2f} | KT={kt_chon:.1f}g "
                    f"[{nuoc_di_chon[0].upper()}]"
                )

            # Hiển thị tiến trình mỗi 5%
            if vong_lap % max(1, self.toi_da_vong_lap // 20) == 0:
                in_tien_trinh(
                    vong_lap / self.toi_da_vong_lap * 100,
                    f"Tabu: vòng {vong_lap}/{self.toi_da_vong_lap}"
                )

        print()  # Xuống dòng sau thanh tiến trình
        in_thong_bao("✔ Tabu Search hoàn thành.")
        return self._xuat_ket_qua()

    # ═══════════════════════════════════════════════════════════
    # XUẤT KẾT QUẢ
    # ═══════════════════════════════════════════════════════════
    def _xuat_ket_qua(self) -> Dict:
        """Đóng gói kết quả tốt nhất thành dict và in ra terminal."""
        in_ket_qua("\n═══════════════════════════════════════")
        in_ket_qua("     KẾT QUẢ LỘ TRÌNH TỐT NHẤT")
        in_ket_qua("═══════════════════════════════════════")
        in_ket_qua(f"  Hàm mục tiêu F = {self.ham_muc_tieu_tot_nhat:.6f}")
        in_ket_qua(f"  Tổng chi phí   = ${self.chi_phi_tot_nhat:.2f} USD")
        in_ket_qua(f"  Tổng khí thải  = {self.khi_thai_tot_nhat:.2f} gram CO2")
        in_ket_qua("═══════════════════════════════════════")

        ket_qua = {
            "ham_muc_tieu":  self.ham_muc_tieu_tot_nhat,
            "tong_chi_phi":  self.chi_phi_tot_nhat,
            "tong_khi_thai": self.khi_thai_tot_nhat,
            "lo_trinh":      {}
        }

        for xe_idx, lo_trinh_mot_xe in enumerate(self.lo_trinh_tot_nhat):
            if xe_idx < len(self.cau_hinh_xe):
                ten_xe  = self.cau_hinh_xe[xe_idx]["ma_xe"]
                loai_xe = self.cau_hinh_xe[xe_idx]["loai_xe"]
            else:
                ten_xe  = f"XE_{xe_idx + 1:02d}"
                loai_xe = "Không rõ"

            ten_cac_kh     = [self.khach_hang[kh]["ten"] for kh in lo_trinh_mot_xe]
            mo_ta_lo_trinh = " → ".join(["[Kho]"] + ten_cac_kh + ["[Kho]"])

            cp_xe, kt_xe, _ = self._danh_gia_mot_xe(lo_trinh_mot_xe)

            ket_qua["lo_trinh"][ten_xe] = {
                "loai_xe":  loai_xe,
                "thu_tu":   lo_trinh_mot_xe,
                "mo_ta":    mo_ta_lo_trinh,
                "chi_phi":  float(cp_xe),
                "khi_thai": float(kt_xe)
            }

            in_ket_qua(f"\n  [{ten_xe} — {loai_xe}]")
            in_ket_qua(f"  {mo_ta_lo_trinh}")
            in_ket_qua(f"  Chi phí: ${cp_xe:.2f} | Khí thải: {kt_xe:.2f}g CO2")

        return ket_qua
