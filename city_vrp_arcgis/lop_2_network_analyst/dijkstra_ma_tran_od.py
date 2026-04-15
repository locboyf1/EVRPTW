"""
=============================================================
LỚP 2: NETWORK ANALYST ENGINE — DIJKSTRA
Nhiệm vụ:
  1. Tải đồ thị đường phố thực từ OSMnx (chạy 1 lần duy nhất)
  2. Snap mỗi điểm khách hàng vào node gần nhất trên đồ thị
  3. Chạy Dijkstra cho từng cặp (i, j) → tích lũy vào 2 Ma trận OD tĩnh:
       - ma_tran_chi_phi[i][j]      = USD (hao mòn xe + lương tài xế)
       - ma_tran_khi_thai_goc[i][j] = GRAM CO2 (chưa nhân hệ số loại xe)
  4. SAU KHI Dijkstra xong, nhân hệ số loại xe vào bản sao ma trận khí thải.

LƯU Ý QUAN TRỌNG VỀ THỨ TỰ CÚ PHÁP:
  - Hệ số loại xe (ví dụ 0.6 của Hybrid) PHẢI được nhân SAU khi Dijkstra
    đã hoàn thành toàn bộ ma trận gốc.
  - Lương tài xế ($26.55/giờ) KHÔNG nhân với hệ số loại xe — đây là
    chi phí tài chính độc lập, chỉ phụ thuộc vào thời gian di chuyển.
=============================================================
"""

import sys
import os

# Thêm đường dẫn gốc vào sys.path
_THU_MUC_GOC = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _THU_MUC_GOC not in sys.path:
    sys.path.insert(0, _THU_MUC_GOC)

import networkx as nx
import numpy as np

try:
    import osmnx as ox
    OSMNX_CO_SAN = True
except ImportError:
    OSMNX_CO_SAN = False

from giao_dien.terminal_ui import in_tieu_de, in_thong_bao, in_canh_bao


# ─────────────────────────────────────────────────────────────
# HẰNG SỐ
# ─────────────────────────────────────────────────────────────
TOC_DO_MAC_DINH_KM_H       = 50      # km/h — dùng khi không có dữ liệu tốc độ
HANG_SO_KHI_THAI_MAC_DINH  = 0.261  # g/km — dùng khi tra bảng MOVES không khớp


# ─────────────────────────────────────────────────────────────
# HÀM: TẠO ĐỒ THỊ TỔNG HỢP DỰ PHÒNG (khi không cài được osmnx)
# ─────────────────────────────────────────────────────────────
def _tao_do_thi_du_phong(tat_ca_diem: list) -> nx.DiGraph:
    """
    Tạo đồ thị đơn giản kết nối đầy đủ giữa các điểm khi osmnx không khả dụng.
    Dùng khoảng cách Euclidean + tốc độ mặc định để ước tính travel_time.
    
    Đây là chế độ FALLBACK — kết quả không chính xác bằng bản đồ thực.
    """
    import math
    in_canh_bao("Đang dùng đồ thị giả (Euclidean) vì OSMnx không khả dụng!")
    G = nx.DiGraph()

    # Thêm node (dùng index làm node_id)
    for i, diem in enumerate(tat_ca_diem):
        G.add_node(i, x=diem["kinh_do"], y=diem["vi_do"])

    # Thêm cạnh kết nối đầy đủ
    DO_KHUECH_DAI_KM_PER_DO = 111.0  # 1 độ lat/lon ≈ 111 km
    for i in range(len(tat_ca_diem)):
        for j in range(len(tat_ca_diem)):
            if i == j:
                continue
            di = tat_ca_diem[i]
            dj = tat_ca_diem[j]
            # Khoảng cách Euclidean (độ) → km → mét
            dx = (dj["kinh_do"] - di["kinh_do"]) * DO_KHUECH_DAI_KM_PER_DO * 1000
            dy = (dj["vi_do"]   - di["vi_do"])   * DO_KHUECH_DAI_KM_PER_DO * 1000
            length_m = math.sqrt(dx * dx + dy * dy)
            toc_do_ms = TOC_DO_MAC_DINH_KM_H * 1000 / 3600  # m/s
            travel_time_s = length_m / toc_do_ms if toc_do_ms > 0 else 0
            G.add_edge(i, j, length=length_m,
                       speed_kph=TOC_DO_MAC_DINH_KM_H,
                       travel_time=travel_time_s)
    return G


# ─────────────────────────────────────────────────────────────
# HÀM: TẢI ĐỒ THỊ ĐƯỜNG PHỐ (OSMnx)
# ─────────────────────────────────────────────────────────────
def tai_ban_do_osm(ten_thanh_pho: str = "Vinh city, Vietnam",
                  ban_kinh_met: int = 8000,
                  tat_ca_diem: list = None) -> object:
    """
    Tải đồ thị đường phố từ OpenStreetMap qua OSMnx.
    Nếu osmnx không cài hoặc kết nối thất bại, dùng đồ thị Euclidean dự phòng.

    Trả về:
        (do_thi, dung_osmnx: bool)
    """
    in_tieu_de("LỚP 2: NETWORK ANALYST — TẢI ĐỒ THỊ")

    if not OSMNX_CO_SAN:
        in_canh_bao("OSMnx chưa được cài đặt. Dùng đồ thị Euclidean dự phòng.")
        if tat_ca_diem is None:
            raise ValueError("Cần truyền tat_ca_diem khi không dùng OSMnx!")
        return _tao_do_thi_du_phong(tat_ca_diem), False

    in_thong_bao(f"Đang tải đồ thị: {ten_thanh_pho} (bán kính {ban_kinh_met}m)...")
    in_canh_bao("⏳ Bước này có thể mất 1–3 phút lần đầu (tải từ OSM server)...")

    try:
        do_thi = ox.graph_from_address(
            ten_thanh_pho,
            network_type="drive",
            dist=ban_kinh_met
        )
        do_thi = ox.add_edge_speeds(do_thi)
        do_thi = ox.add_edge_travel_times(do_thi)
        in_thong_bao(f"✔ Đã tải đồ thị OSM: {len(do_thi.nodes):,} nút | {len(do_thi.edges):,} cạnh")
        return do_thi, True

    except Exception as loi:
        in_canh_bao(f"Tải OSM thất bại ({loi}). Chuyển sang đồ thị dự phòng.")
        if tat_ca_diem is None:
            raise
        return _tao_do_thi_du_phong(tat_ca_diem), False


# ─────────────────────────────────────────────────────────────
# HÀM: SNAP ĐIỂM VÀO NODE GẦN NHẤT
# ─────────────────────────────────────────────────────────────
def snap_diem_vao_do_thi(do_thi,
                          tat_ca_diem: list,
                          dung_osmnx: bool = True) -> list:
    """
    Tìm node đồ thị gần nhất cho mỗi điểm (kho + khách hàng).
    
    - Nếu dùng OSMnx: dùng ox.distance.nearest_nodes()
    - Nếu dùng đồ thị dự phòng: node_id = index của điểm
    
    Trả về:
        danh_sach_node: list[int]
    """
    in_thong_bao("Đang snap các điểm vào mạng lưới đường phố...")

    if not dung_osmnx:
        # Đồ thị dự phòng: node_id chính là index của điểm
        danh_sach_node = list(range(len(tat_ca_diem)))
        for i, diem in enumerate(tat_ca_diem):
            in_thong_bao(f"  [{i:02d}] {diem['ten']:25s} → Node (Euclidean): {i}")
        return danh_sach_node

    danh_sach_node = []
    for i, diem in enumerate(tat_ca_diem):
        node_gan_nhat = ox.distance.nearest_nodes(
            do_thi,
            X=diem["kinh_do"],
            Y=diem["vi_do"]
        )
        danh_sach_node.append(node_gan_nhat)
        in_thong_bao(f"  [{i:02d}] {diem['ten']:25s} → Node OSM: {node_gan_nhat}")

    return danh_sach_node


# ─────────────────────────────────────────────────────────────
# HÀM CHÍNH: TẠO MA TRẬN OD BẰNG DIJKSTRA
# ─────────────────────────────────────────────────────────────
def tao_ma_tran_od_bang_dijkstra(
        do_thi,
        danh_sach_node_osm: list,
        cau_hinh_xe: dict,
        luong_tai_xe_usd_per_gio: float,
        bang_moves: dict
) -> tuple:
    """
    GIAI ĐOẠN 1 (ArcGIS Clone): Dijkstra chạy MỘT LẦN DUY NHẤT để xây dựng
    2 Ma trận OD tĩnh N×N. Tabu Search sau đó chỉ tra cứu 2 mảng này.

    LUỒNG XỬ LÝ:
    ┌─────────────────────────────────────────────────────────┐
    │  For i in range(N):                                     │
    │    For j in range(N):                                   │
    │      1. Dijkstra(node_i → node_j) → danh_sach_node     │
    │      2. Tích lũy chiều dài (m) và thời gian (s)        │
    │      3. Tính chi_phi = hao_mon + luong_tai_xe           │
    │      4. Tính khi_thai_goc = quang_duong × he_so_MOVES  │
    │  END Dijkstra (vòng lặp kết thúc hoàn toàn)            │
    │                                                         │
    │  SAU ĐÓ (ngoài vòng lặp Dijkstra):                     │
    │    ma_tran_khi_thai_xe = ma_tran_goc × he_so_xe        │
    └─────────────────────────────────────────────────────────┘

    Tham số:
        cau_hinh_xe: dict cấu hình MỘT xe (dùng tính chi phí hao mòn)
        bang_moves:  dict {toc_do_kmh_int: he_so_khi_thai_float}

    Trả về:
        (ma_tran_chi_phi, ma_tran_khi_thai_goc,
         ma_tran_thoi_gian_giay, ma_tran_quang_duong_km)
        Tất cả là numpy array N×N.
        ⚠ ma_tran_khi_thai_goc CHƯA nhân hệ số loại xe.
    """
    in_tieu_de("LỚP 2: DIJKSTRA — XÂY DỰNG MA TRẬN OD")

    so_diem = len(danh_sach_node_osm)
    chi_phi_hao_mon_per_km = cau_hinh_xe["chi_phi_hao_mon_usd_per_km"]

    # --- Khởi tạo 4 ma trận rỗng N×N ---
    ma_tran_chi_phi        = np.zeros((so_diem, so_diem))
    ma_tran_khi_thai_goc   = np.zeros((so_diem, so_diem))
    ma_tran_thoi_gian_giay = np.zeros((so_diem, so_diem))
    ma_tran_quang_duong_km = np.zeros((so_diem, so_diem))

    tong_cap = so_diem * so_diem
    dem = 0

    in_thong_bao(f"Dijkstra đang xử lý {so_diem}×{so_diem} = {tong_cap} cặp điểm...")
    in_canh_bao("⏳ Bước này là nút cổ chai — chạy một lần duy nhất rồi lưu cache...")

    # ═══════════════════════════════════════════════════════════
    # VÒNG LẶP DÒ ĐƯỜNG DIJKSTRA
    # (Toàn bộ vòng lặp này PHẢI chạy xong trước khi nhân hệ số xe)
    # ═══════════════════════════════════════════════════════════
    for i in range(so_diem):
        for j in range(so_diem):
            dem += 1

            if i == j:
                continue

            node_nguon = danh_sach_node_osm[i]
            node_dich  = danh_sach_node_osm[j]

            try:
                # ── DIJKSTRA: Tìm đường ngắn nhất theo travel_time ──
                duong_di_nodes = nx.shortest_path(
                    do_thi,
                    source=node_nguon,
                    target=node_dich,
                    weight="travel_time"
                )

                # ── Tích lũy chiều dài (m) và thời gian (s) qua từng cạnh ──
                tong_chieu_dai_m = 0.0
                tong_thoi_gian_s = 0.0

                for k in range(len(duong_di_nodes) - 1):
                    node_hien  = duong_di_nodes[k]
                    node_tiep  = duong_di_nodes[k + 1]
                    du_lieu_canh_raw = do_thi[node_hien][node_tiep]

                    # Phân biệt 2 loại đồ thị:
                    # - MultiDiGraph (OSMnx): du_lieu_canh_raw = {0: {attrs}, 1: {attrs}, ...}
                    #   → giá trị là dict thuộc tính → dùng .values() để lấy
                    # - DiGraph (đồ thị dự phòng): du_lieu_canh_raw = {attrs} trực tiếp
                    #   → giá trị là scalar (float/str) → dùng như dict thông thường
                    if isinstance(do_thi, nx.MultiDiGraph):
                        canh_tot_nhat = min(
                            du_lieu_canh_raw.values(),
                            key=lambda c: c.get("travel_time", float("inf"))
                        )
                    else:
                        # DiGraph: lấy thuộc tính trực tiếp từ dict cạnh
                        canh_tot_nhat = du_lieu_canh_raw

                    tong_chieu_dai_m += canh_tot_nhat.get("length", 0)
                    tong_thoi_gian_s += canh_tot_nhat.get("travel_time", 0)

                # Chuyển đổi đơn vị
                tong_chieu_dai_km  = tong_chieu_dai_m  / 1000.0
                tong_thoi_gian_gio = tong_thoi_gian_s  / 3600.0

                # ── Tính tốc độ trung bình để tra bảng MOVES ──
                if tong_thoi_gian_gio > 0:
                    toc_do_tb_kmh = tong_chieu_dai_km / tong_thoi_gian_gio
                else:
                    toc_do_tb_kmh = TOC_DO_MAC_DINH_KM_H

                # Làm tròn tới bội số 10 gần nhất, kẹp trong [20, 120]
                toc_do_tra_bang = max(20, min(120, round(toc_do_tb_kmh / 10) * 10))
                he_so_khi_thai_moves = bang_moves.get(
                    toc_do_tra_bang, HANG_SO_KHI_THAI_MAC_DINH
                )

                # ── Tính chi phí (USD) ──
                # = Hao mòn + Lương tài xế (lương là biến ĐỘC LẬP, không nhân hệ số xe)
                chi_phi_hao_mon_usd = tong_chieu_dai_km * chi_phi_hao_mon_per_km
                chi_phi_luong_usd   = tong_thoi_gian_gio * luong_tai_xe_usd_per_gio
                tong_chi_phi_usd    = chi_phi_hao_mon_usd + chi_phi_luong_usd

                # ── Tính khí thải gốc (gram CO2) ──
                # CHƯA nhân hệ số loại xe — sẽ nhân NGOÀI vòng lặp này
                khi_thai_goc_gram = tong_chieu_dai_km * he_so_khi_thai_moves

                # ── Ghi vào ma trận ──
                ma_tran_chi_phi[i][j]        = tong_chi_phi_usd
                ma_tran_khi_thai_goc[i][j]   = khi_thai_goc_gram
                ma_tran_thoi_gian_giay[i][j] = tong_thoi_gian_s
                ma_tran_quang_duong_km[i][j]  = tong_chieu_dai_km

            except (nx.NetworkXNoPath, nx.NodeNotFound):
                in_canh_bao(f"  [!] Không tìm được đường: {i}→{j}, gán ∞")
                ma_tran_chi_phi[i][j]        = 1e9
                ma_tran_khi_thai_goc[i][j]   = 1e9
                ma_tran_thoi_gian_giay[i][j] = 1e9
                ma_tran_quang_duong_km[i][j]  = 1e9

            # Hiển thị tiến trình mỗi 10%
            if dem % max(1, tong_cap // 10) == 0:
                phan_tram = dem / tong_cap * 100
                from giao_dien.terminal_ui import in_tien_trinh
                in_tien_trinh(phan_tram, f"Dijkstra: {dem}/{tong_cap} cặp")

    # Xuống dòng sau thanh tiến trình
    print()
    in_thong_bao("OK - Dijkstra hoan thanh. 4 Ma tran OD goc da san sang.")
    
    # Kiểm tra xem có giá trị nào hợp lệ (lớn hơn 0 và nhỏ hơn vô cùng) không
    hop_le = ma_tran_chi_phi[(ma_tran_chi_phi > 0) & (ma_tran_chi_phi < 1e8)]
    if hop_le.size > 0:
        in_thong_bao(
            f"   Chi phi: min={hop_le.min():.2f}$ | max={hop_le.max():.2f}$"
        )
    else:
        in_canh_bao("   [!] Canh bao: Ma tran chi phi khong co du lieu hop le (co the do loi snap diem).")

    # ═══════════════════════════════════════════════════════════
    # DIJKSTRA KẾT THÚC — Trả về ma trận gốc (chưa nhân hệ số xe)
    # Hàm ap_dung_he_so_loai_xe() sẽ được gọi NGOÀI hàm này
    # ═══════════════════════════════════════════════════════════
    return (
        ma_tran_chi_phi,
        ma_tran_khi_thai_goc,
        ma_tran_thoi_gian_giay,
        ma_tran_quang_duong_km
    )


# ─────────────────────────────────────────────────────────────
# HÀM PHỤ: NHÂN HỆ SỐ LOẠI XE SAU DIJKSTRA
# ⚠ GỌI SAU KHI tao_ma_tran_od_bang_dijkstra() ĐÃ HOÀN THÀNH
# ─────────────────────────────────────────────────────────────
def ap_dung_he_so_loai_xe(ma_tran_khi_thai_goc: np.ndarray,
                           he_so_khi_thai_xe: float) -> np.ndarray:
    """
    Nhân hệ số loại xe vào ma trận khí thải gốc BẰNG NUMPY BROADCASTING.
    Việc này thực hiện sau khi Dijkstra đã hoàn tất toàn bộ — không bao giờ
    được đặt trong vòng lặp for i, for j của Dijkstra.

    Ví dụ:
        Xe Hybrid: he_so_khi_thai = 0.6
        → Kết quả = ma_tran_goc × 0.6 (giảm 40% khí thải so với baseline)

    Trả về:
        numpy array N×N đã nhân hệ số xe
    """
    ma_tran_khi_thai_xe = ma_tran_khi_thai_goc * he_so_khi_thai_xe
    in_thong_bao(
        f"✔ Đã áp dụng hệ số loại xe: ×{he_so_khi_thai_xe} "
        f"(Khí thải giảm {(1 - he_so_khi_thai_xe) * 100:.0f}% so với baseline)"
    )
    return ma_tran_khi_thai_xe
