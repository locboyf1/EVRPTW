# 🗺️ Hệ Thống City VRP Đa Mục Tiêu — Bản Sao ArcGIS Network Analyst

> **Mục tiêu**: Tái hiện chính xác phương pháp luận của bài báo khoa học dùng ArcGIS VRP Solver.  
> **Kiến trúc**: 3 lớp tách biệt — Tiền xử lý → Dijkstra (Network Analyst) → Tabu Search (VRP Solver)  
> **Nguyên tắc cốt lõi**: Tabu Search **TUYỆT ĐỐI** chỉ đọc từ Ma trận OD tĩnh, không bao giờ gọi đồ thị

---

## 📁 Cấu Trúc Thư Mục

```
city_vrp_arcgis/
│
├── du_lieu/                          # Lớp 1: Dữ liệu đầu vào
│   ├── du_lieu_khi_thai.json         # Bảng MOVES: tốc độ → hệ số xả thải
│   ├── cau_hinh_xe.json              # Cấu hình đội xe (hao mòn, khí thải, lương)
│   └── khach_hang.json               # Danh sách khách hàng + time windows
│
├── lop_1_tien_xu_ly/
│   └── tao_du_lieu.py                # Script sinh JSON tĩnh
│
├── lop_2_network_analyst/
│   └── dijkstra_ma_tran_od.py        # Tải đồ thị OSMnx + chạy Dijkstra → 2 ma trận
│
├── lop_3_vrp_solver/
│   └── tabu_search_vrp.py            # Class TabuSearchVRPSolver (tự xây, không OR-Tools)
│
├── giao_dien/
│   └── terminal_ui.py                # Giao diện terminal minimalist màu xanh pastel
│
└── main.py                           # Điểm khởi động — điều phối 3 lớp theo thứ tự
```

---

## 📄 File 1: `du_lieu/du_lieu_khi_thai.json`

```json
{
  "_ghi_chu": "Bảng MOVES (Motor Vehicle Emission Simulator) — mapping tốc độ giới hạn → hệ số xả thải CO2 (g/km)",
  "bang_moves": {
    "20":  0.312,
    "30":  0.285,
    "40":  0.261,
    "50":  0.248,
    "60":  0.239,
    "70":  0.244,
    "80":  0.258,
    "90":  0.275,
    "100": 0.298,
    "110": 0.324,
    "120": 0.356
  },
  "he_so_mac_dinh_khi_khong_co_du_lieu": 0.261
}
```

---

## 📄 File 2: `du_lieu/cau_hinh_xe.json`

```json
{
  "_ghi_chu": "Cấu hình đội xe. Hệ số khí thải nhân VÀO MA TRẬN sau Dijkstra, KHÔNG nhân trong vòng lặp dò đường. Lương tài xế là biến ĐỘC LẬP theo thời gian.",
  "luong_tai_xe_usd_per_gio": 26.55,
  "danh_sach_xe": [
    {
      "ma_xe": "XE_01",
      "loai_xe": "Diesel",
      "tai_trong_kg": 5000,
      "chi_phi_hao_mon_usd_per_km": 0.15,
      "he_so_khi_thai": 1.0,
      "_ghi_chu_he_so": "Xe Diesel = baseline 1.0, không điều chỉnh"
    },
    {
      "ma_xe": "XE_02",
      "loai_xe": "Hybrid",
      "tai_trong_kg": 4500,
      "chi_phi_hao_mon_usd_per_km": 0.18,
      "he_so_khi_thai": 0.6,
      "_ghi_chu_he_so": "Xe Hybrid phát thải ít hơn 40% so với Diesel"
    },
    {
      "ma_xe": "XE_03",
      "loai_xe": "Diesel",
      "tai_trong_kg": 5000,
      "chi_phi_hao_mon_usd_per_km": 0.15,
      "he_so_khi_thai": 1.0,
      "_ghi_chu_he_so": "Xe Diesel thứ hai"
    }
  ]
}
```

---

## 📄 File 3: `du_lieu/khach_hang.json`

```json
{
  "_ghi_chu": "Danh sách khách hàng. ID 0 = Kho (Depot). Tọa độ là lat/lon thực tế TP.HCM. Thời gian tính bằng phút từ 0h00.",
  "kho_xuat_phat": {
    "ma_khach": 0,
    "ten": "Kho Trung Tâm",
    "vi_do": 10.7769,
    "kinh_do": 106.7009,
    "thoi_gian_mo_cua": 0,
    "thoi_gian_dong_cua": 1440,
    "thoi_gian_boc_do": 0,
    "nhu_cau_hang_kg": 0
  },
  "danh_sach_khach_hang": [
    {
      "ma_khach": 1, "ten": "Siêu thị An Phú",
      "vi_do": 10.8010, "kinh_do": 106.7327,
      "thoi_gian_mo_cua": 480, "thoi_gian_dong_cua": 720,
      "thoi_gian_boc_do": 20, "nhu_cau_hang_kg": 500
    },
    {
      "ma_khach": 2, "ten": "Chợ Bình Thạnh",
      "vi_do": 10.8136, "kinh_do": 106.7100,
      "thoi_gian_mo_cua": 360, "thoi_gian_dong_cua": 600,
      "thoi_gian_boc_do": 15, "nhu_cau_hang_kg": 350
    },
    {
      "ma_khach": 3, "ten": "Cửa hàng Quận 1",
      "vi_do": 10.7769, "kinh_do": 106.6981,
      "thoi_gian_mo_cua": 540, "thoi_gian_dong_cua": 780,
      "thoi_gian_boc_do": 10, "nhu_cau_hang_kg": 200
    },
    {
      "ma_khach": 4, "ten": "Kho Thủ Đức",
      "vi_do": 10.8500, "kinh_do": 106.7510,
      "thoi_gian_mo_cua": 420, "thoi_gian_dong_cua": 660,
      "thoi_gian_boc_do": 25, "nhu_cau_hang_kg": 800
    },
    {
      "ma_khach": 5, "ten": "Đại lý Gò Vấp",
      "vi_do": 10.8389, "kinh_do": 106.6652,
      "thoi_gian_mo_cua": 480, "thoi_gian_dong_cua": 720,
      "thoi_gian_boc_do": 18, "nhu_cau_hang_kg": 420
    },
    {
      "ma_khach": 6, "ten": "Shop Tân Bình",
      "vi_do": 10.8017, "kinh_do": 106.6530,
      "thoi_gian_mo_cua": 360, "thoi_gian_dong_cua": 570,
      "thoi_gian_boc_do": 12, "nhu_cau_hang_kg": 300
    },
    {
      "ma_khach": 7, "ten": "Trung tâm Quận 7",
      "vi_do": 10.7397, "kinh_do": 106.7196,
      "thoi_gian_mo_cua": 510, "thoi_gian_dong_cua": 750,
      "thoi_gian_boc_do": 20, "nhu_cau_hang_kg": 450
    },
    {
      "ma_khach": 8, "ten": "Cửa hàng Bình Chánh",
      "vi_do": 10.6820, "kinh_do": 106.6130,
      "thoi_gian_mo_cua": 540, "thoi_gian_dong_cua": 810,
      "thoi_gian_boc_do": 30, "nhu_cau_hang_kg": 600
    }
  ]
}
```

---

## 📄 File 4: `lop_1_tien_xu_ly/tao_du_lieu.py`

```python
"""
=============================================================
LỚP 1: TIỀN XỬ LÝ DỮ LIỆU
Nhiệm vụ: Đọc và xác thực các file JSON cấu hình.
          Sinh mảng Python thuần túy để truyền vào Lớp 2 & 3.
=============================================================
"""

import json
import os
from giao_dien.terminal_ui import in_tieu_de, in_thong_bao, in_canh_bao, in_loi


# ─────────────────────────────────────────────────────────────
# HÀM: ĐỌC FILE JSON AN TOÀN
# ─────────────────────────────────────────────────────────────
def doc_json(duong_dan_file: str) -> dict:
    """Đọc file JSON và trả về dict Python. Báo lỗi rõ ràng nếu không tìm thấy."""
    if not os.path.exists(duong_dan_file):
        in_loi(f"Không tìm thấy file: {duong_dan_file}")
        raise FileNotFoundError(f"File không tồn tại: {duong_dan_file}")
    with open(duong_dan_file, "r", encoding="utf-8") as f:
        du_lieu = json.load(f)
    in_thong_bao(f"✔ Đã đọc: {duong_dan_file}")
    return du_lieu


# ─────────────────────────────────────────────────────────────
# HÀM CHÍNH: TẢI VÀ XÁC THỰC TOÀN BỘ DỮ LIỆU
# ─────────────────────────────────────────────────────────────
def tai_va_xu_ly_du_lieu(thu_muc_du_lieu: str = "du_lieu") -> dict:
    """
    Đọc 3 file JSON, xác thực tính hợp lệ và trả về dict tổng hợp.
    
    Trả về:
        {
            'bang_moves':       dict {toc_do_str: he_so_float},
            'cau_hinh_xe':      list[dict] (danh sách các xe),
            'luong_tai_xe':     float (USD/giờ),
            'kho':              dict (thông tin kho xuất phát),
            'khach_hang':       list[dict] (danh sách KH, không kể kho),
            'tat_ca_diem':      list[dict] (kho + KH, index 0 = kho)
        }
    """
    in_tieu_de("LỚP 1: TIỀN XỬ LÝ DỮ LIỆU")

    # --- Đọc 3 file JSON ---
    du_lieu_khi_thai = doc_json(os.path.join(thu_muc_du_lieu, "du_lieu_khi_thai.json"))
    cau_hinh_xe_json = doc_json(os.path.join(thu_muc_du_lieu, "cau_hinh_xe.json"))
    khach_hang_json  = doc_json(os.path.join(thu_muc_du_lieu, "khach_hang.json"))

    # --- Trích xuất bảng MOVES ---
    bang_moves = {
        int(k): float(v)
        for k, v in du_lieu_khi_thai["bang_moves"].items()
    }

    # --- Trích xuất cấu hình xe ---
    danh_sach_xe = cau_hinh_xe_json["danh_sach_xe"]
    luong_tai_xe = float(cau_hinh_xe_json["luong_tai_xe_usd_per_gio"])

    # --- Trích xuất danh sách điểm ---
    kho    = khach_hang_json["kho_xuat_phat"]
    diem_kh = khach_hang_json["danh_sach_khach_hang"]

    # Gộp: index 0 = kho, 1..N = khách hàng
    tat_ca_diem = [kho] + diem_kh

    # --- Xác thực ---
    _xac_thuc_du_lieu(tat_ca_diem, danh_sach_xe)

    in_thong_bao(f"✔ Tổng số điểm (kho + khách hàng): {len(tat_ca_diem)}")
    in_thong_bao(f"✔ Số xe trong đội:                  {len(danh_sach_xe)}")
    in_thong_bao(f"✔ Mức lương tài xế:                 ${luong_tai_xe}/giờ (biến độc lập theo thời gian)")

    return {
        "bang_moves":    bang_moves,
        "cau_hinh_xe":   danh_sach_xe,
        "luong_tai_xe":  luong_tai_xe,
        "kho":           kho,
        "khach_hang":    diem_kh,
        "tat_ca_diem":   tat_ca_diem,
    }


# ─────────────────────────────────────────────────────────────
# HÀM PHỤ: XÁC THỰC DỮ LIỆU
# ─────────────────────────────────────────────────────────────
def _xac_thuc_du_lieu(tat_ca_diem: list, danh_sach_xe: list):
    """Kiểm tra tính hợp lệ cơ bản của dữ liệu đầu vào."""
    for diem in tat_ca_diem:
        # Kiểm tra time window hợp lệ
        if diem["thoi_gian_mo_cua"] > diem["thoi_gian_dong_cua"]:
            raise ValueError(
                f"[LỖI] Điểm '{diem['ten']}': "
                f"thoi_gian_mo_cua ({diem['thoi_gian_mo_cua']}) "
                f"> thoi_gian_dong_cua ({diem['thoi_gian_dong_cua']})"
            )
    for xe in danh_sach_xe:
        if xe["he_so_khi_thai"] <= 0:
            raise ValueError(f"[LỖI] Xe '{xe['ma_xe']}': he_so_khi_thai phải > 0")
    in_thong_bao("✔ Xác thực dữ liệu: Hợp lệ")
```

---

## 📄 File 5: `lop_2_network_analyst/dijkstra_ma_tran_od.py`

```python
"""
=============================================================
LỚP 2: NETWORK ANALYST ENGINE — DIJKSTRA
Nhiệm vụ:
  1. Tải đồ thị đường phố thực từ OSMnx (chạy 1 lần duy nhất)
  2. Snap mỗi điểm khách hàng vào node gần nhất trên đồ thị
  3. Chạy Dijkstra cho từng cặp (i, j) → tích lũy vào 2 Ma trận OD tĩnh:
       - ma_tran_chi_phi[i][j]  = USD (hao mòn xe + lương tài xế)
       - ma_tran_khi_thai[i][j] = GRAM CO2 (chưa nhân hệ số loại xe)
  4. SAU KHI Dijkstra xong, nhân hệ số loại xe vào bản sao ma trận khí thải.

LƯU Ý QUAN TRỌNG VỀ THỨ TỰ CÚ PHÁP:
  - Hệ số loại xe (ví dụ 0.6 của Hybrid) PHẢI được nhân SAU khi Dijkstra
    đã hoàn thành toàn bộ ma trận gốc.
  - Lương tài xế ($26.55/giờ) KHÔNG nhân với hệ số loại xe — đây là
    chi phí tài chính độc lập, chỉ phụ thuộc vào thời gian di chuyển.
=============================================================
"""

import math
import osmnx as ox
import networkx as nx
import numpy as np
from giao_dien.terminal_ui import in_tieu_de, in_thong_bao, in_canh_bao, in_tien_trinh


# ─────────────────────────────────────────────────────────────
# HẰNG SỐ
# ─────────────────────────────────────────────────────────────
TOC_DO_MAC_DINH_KM_H = 50       # km/h — dùng khi không có dữ liệu tốc độ đường
HANG_SO_KHI_THAI_MAC_DINH = 0.261  # g/km — tra bảng MOVES khi speed không khớp


# ─────────────────────────────────────────────────────────────
# HÀM: TẢI ĐỒ THỊ ĐƯỜNG PHỐ (OSMnx)
# ─────────────────────────────────────────────────────────────
def tai_do_thi_duong_pho(ten_thanh_pho: str = "Ho Chi Minh City, Vietnam",
                          ban_kinh_met: int = 8000) -> nx.MultiDiGraph:
    """
    Tải đồ thị đường phố từ OpenStreetMap qua OSMnx.
    Chỉ tải đường dành cho xe hơi (network_type='drive').
    Thêm tốc độ và thời gian di chuyển cho từng cạnh đồ thị.

    Tham số:
        ten_thanh_pho: Tên thành phố/khu vực để tải bản đồ
        ban_kinh_met:  Bán kính tải tính từ trung tâm (mét)

    Trả về:
        do_thi: nx.MultiDiGraph với thuộc tính 'length' (m), 'speed_kph', 'travel_time' (s)
    """
    in_tieu_de("LỚP 2: NETWORK ANALYST — TẢI ĐỒ THỊ")
    in_thong_bao(f"Đang tải đồ thị: {ten_thanh_pho} (bán kính {ban_kinh_met}m)...")
    in_canh_bao("⏳ Bước này có thể mất 1-3 phút lần đầu (tải từ OSM server)...")

    # Tải đồ thị đường xe hơi từ OSMnx
    do_thi = ox.graph_from_place(
        ten_thanh_pho,
        network_type="drive",
        dist=ban_kinh_met
    )

    # Thêm tốc độ (km/h) và thời gian di chuyển (giây) cho từng cạnh
    do_thi = ox.add_edge_speeds(do_thi)       # Thêm speed_kph dựa trên maxspeed OSM
    do_thi = ox.add_edge_travel_times(do_thi) # Thêm travel_time = length / speed

    in_thong_bao(f"✔ Đã tải đồ thị: {len(do_thi.nodes):,} nút | {len(do_thi.edges):,} cạnh")
    return do_thi


# ─────────────────────────────────────────────────────────────
# HÀM: SNAP ĐIỂM VÀO NODE GẦN NHẤT TRÊN ĐỒ THỊ
# ─────────────────────────────────────────────────────────────
def snap_diem_vao_do_thi(do_thi: nx.MultiDiGraph,
                          tat_ca_diem: list) -> list:
    """
    Tìm node OSM gần nhất cho mỗi điểm (kho + khách hàng).
    Đây là bước 'Network Location' trong ArcGIS Network Analyst.

    Trả về:
        danh_sach_node_osm: list[int] — node_id OSM tương ứng với từng điểm
    """
    in_thong_bao("Đang snap các điểm vào mạng lưới đường phố...")
    danh_sach_node_osm = []

    for i, diem in enumerate(tat_ca_diem):
        node_gan_nhat = ox.distance.nearest_nodes(
            do_thi,
            X=diem["kinh_do"],   # Longitude = X
            Y=diem["vi_do"]      # Latitude  = Y
        )
        danh_sach_node_osm.append(node_gan_nhat)
        in_thong_bao(f"  [{i:02d}] {diem['ten']:25s} → Node OSM: {node_gan_nhat}")

    return danh_sach_node_osm


# ─────────────────────────────────────────────────────────────
# HÀM PHỤ: LẤY TỐC ĐỘ TRUNG BÌNH CỦA MỘT ĐƯỜNG ĐI
# ─────────────────────────────────────────────────────────────
def _lay_toc_do_trung_binh_duong_di(do_thi: nx.MultiDiGraph,
                                     danh_sach_node_tren_duong: list) -> float:
    """
    Tính tốc độ trung bình có trọng số (theo km) của một đường đi (list of nodes).
    Dùng để tra bảng MOVES: tốc độ → hệ số khí thải.
    """
    tong_chieu_dai = 0.0
    tong_chieu_dai_x_toc_do = 0.0

    for k in range(len(danh_sach_node_tren_duong) - 1):
        node_hien = danh_sach_node_tren_duong[k]
        node_tiep  = danh_sach_node_tren_duong[k + 1]

        # Lấy dữ liệu cạnh (chọn cạnh có travel_time nhỏ nhất nếu có song song)
        du_lieu_canh = min(
            do_thi[node_hien][node_tiep].values(),
            key=lambda c: c.get("travel_time", float("inf"))
        )
        chieu_dai_canh_m = du_lieu_canh.get("length", 0)        # mét
        toc_do_canh_kmh  = du_lieu_canh.get("speed_kph", TOC_DO_MAC_DINH_KM_H)

        tong_chieu_dai            += chieu_dai_canh_m
        tong_chieu_dai_x_toc_do   += chieu_dai_canh_m * toc_do_canh_kmh

    if tong_chieu_dai == 0:
        return TOC_DO_MAC_DINH_KM_H

    return tong_chieu_dai_x_toc_do / tong_chieu_dai


# ─────────────────────────────────────────────────────────────
# HÀM CHÍNH: TẠO MA TRẬN OD BẰNG DIJKSTRA
# (Đây là hàm mô phỏng lõi ArcGIS Network Analyst)
# ─────────────────────────────────────────────────────────────
def tao_ma_tran_od_bang_dijkstra(
        do_thi: nx.MultiDiGraph,
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
    │      3. Tính chi phí = hao_mon + luong_tai_xe           │
    │      4. Tính khi_thai_goc = quang_duong × he_so_MOVES  │
    │  END Dijkstra                                           │
    │                                                         │
    │  SAU ĐÓ (ngoài vòng lặp Dijkstra):                     │
    │    ma_tran_khi_thai_xe = ma_tran_khi_thai_goc × he_so_xe│
    └─────────────────────────────────────────────────────────┘

    Tham số:
        cau_hinh_xe: dict cấu hình MỘT xe (dùng tính chi phí hao mòn)
        bang_moves:  dict {toc_do_kmh: he_so_khi_thai}

    Trả về:
        (ma_tran_chi_phi, ma_tran_khi_thai_goc, ma_tran_thoi_gian_giay,
         ma_tran_quang_duong_km)
        Tất cả là numpy array N×N.
        ma_tran_khi_thai_goc: CHƯA nhân hệ số loại xe — hàm gọi ngoài sẽ nhân sau.
    """
    in_tieu_de("LỚP 2: DIJKSTRA — XÂY DỰNG MA TRẬN OD")

    so_diem = len(danh_sach_node_osm)
    chi_phi_hao_mon = cau_hinh_xe["chi_phi_hao_mon_usd_per_km"]  # USD/km

    # --- Khởi tạo 4 ma trận rỗng N×N ---
    ma_tran_chi_phi        = np.zeros((so_diem, so_diem))  # USD
    ma_tran_khi_thai_goc   = np.zeros((so_diem, so_diem))  # gram CO2 (chưa nhân hệ số xe)
    ma_tran_thoi_gian_giay = np.zeros((so_diem, so_diem))  # giây
    ma_tran_quang_duong_km = np.zeros((so_diem, so_diem))  # km

    tong_cap = so_diem * so_diem
    dem = 0

    in_thong_bao(f"Dijkstra đang xử lý {so_diem}×{so_diem} = {tong_cap} cặp điểm...")
    in_canh_bao("⏳ Bước này là nút cổ chai — chạy một lần duy nhất rồi lưu cache...")

    # ═══════════════════════════════════════════════════════════
    # VÒNG LẶP DÒ ĐƯỜNG DIJKSTRA (chạy xong hoàn toàn trước)
    # ═══════════════════════════════════════════════════════════
    for i in range(so_diem):
        for j in range(so_diem):
            dem += 1

            # Đường chéo: cùng điểm, chi phí = 0
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
                    weight="travel_time"  # Tối ưu theo thời gian (như ArcGIS mặc định)
                )

                # ── Tích lũy chiều dài (m) và thời gian (s) qua từng cạnh ──
                tong_chieu_dai_m = 0.0
                tong_thoi_gian_s = 0.0

                for k in range(len(duong_di_nodes) - 1):
                    node_hien = duong_di_nodes[k]
                    node_tiep  = duong_di_nodes[k + 1]
                    canh_tot_nhat = min(
                        do_thi[node_hien][node_tiep].values(),
                        key=lambda c: c.get("travel_time", float("inf"))
                    )
                    tong_chieu_dai_m += canh_tot_nhat.get("length", 0)
                    tong_thoi_gian_s += canh_tot_nhat.get("travel_time", 0)

                # Chuyển đổi đơn vị
                tong_chieu_dai_km = tong_chieu_dai_m / 1000.0
                tong_thoi_gian_gio = tong_thoi_gian_s / 3600.0

                # ── Tính tốc độ trung bình để tra bảng MOVES ──
                toc_do_tb_kmh = (tong_chieu_dai_km / tong_thoi_gian_gio
                                 if tong_thoi_gian_gio > 0 else TOC_DO_MAC_DINH_KM_H)

                # Làm tròn xuống bội số 10 gần nhất để tra bảng MOVES
                toc_do_tra_bang = max(20, min(120, round(toc_do_tb_kmh / 10) * 10))
                he_so_khi_thai_moves = bang_moves.get(toc_do_tra_bang, HANG_SO_KHI_THAI_MAC_DINH)

                # ── Tính chi phí = hao mòn + lương tài xế ──
                chi_phi_hao_mon_usd   = tong_chieu_dai_km * chi_phi_hao_mon     # USD
                chi_phi_luong_usd     = tong_thoi_gian_gio * luong_tai_xe_usd_per_gio  # USD
                tong_chi_phi_usd      = chi_phi_hao_mon_usd + chi_phi_luong_usd

                # ── Tính khí thải gốc (CHƯA nhân hệ số loại xe) ──
                khi_thai_goc_gram = tong_chieu_dai_km * he_so_khi_thai_moves     # gram CO2

                # ── Ghi vào ma trận ──
                ma_tran_chi_phi[i][j]        = tong_chi_phi_usd
                ma_tran_khi_thai_goc[i][j]   = khi_thai_goc_gram
                ma_tran_thoi_gian_giay[i][j] = tong_thoi_gian_s
                ma_tran_quang_duong_km[i][j]  = tong_chieu_dai_km

            except nx.NetworkXNoPath:
                in_canh_bao(f"  [!] Không tìm được đường: {i} → {j}, gán giá trị vô cực")
                ma_tran_chi_phi[i][j]        = float("inf")
                ma_tran_khi_thai_goc[i][j]   = float("inf")
                ma_tran_thoi_gian_giay[i][j] = float("inf")
                ma_tran_quang_duong_km[i][j]  = float("inf")

            # Hiển thị tiến trình mỗi 10%
            if dem % max(1, tong_cap // 10) == 0:
                phan_tram = dem / tong_cap * 100
                in_tien_trinh(phan_tram, f"Dijkstra: {dem}/{tong_cap} cặp")

    in_thong_bao("✔ Dijkstra hoàn thành. Ma trận OD gốc đã sẵn sàng.")

    # ═══════════════════════════════════════════════════════════
    # SAU KHI DIJKSTRA XONG: Nhân hệ số loại xe vào khí thải
    # (TÁCH BIỆT hoàn toàn khỏi vòng lặp Dijkstra ở trên)
    # ═══════════════════════════════════════════════════════════
    # Hàm này trả về ma_tran_khi_thai_goc (chưa nhân hệ số)
    # Việc nhân hệ số sẽ do hàm gọi bên ngoài thực hiện — xem main.py
    return (
        ma_tran_chi_phi,
        ma_tran_khi_thai_goc,
        ma_tran_thoi_gian_giay,
        ma_tran_quang_duong_km
    )


# ─────────────────────────────────────────────────────────────
# HÀM PHỤ: NHÂN HỆ SỐ LOẠI XE SAU DIJKSTRA
# (Hàm này gọi NGOÀI và SAU vòng lặp Dijkstra)
# ─────────────────────────────────────────────────────────────
def ap_dung_he_so_loai_xe(ma_tran_khi_thai_goc: np.ndarray,
                           he_so_khi_thai_xe: float) -> np.ndarray:
    """
    Nhân hệ số loại xe vào ma trận khí thải gốc.
    
    VÍ DỤ: Xe Hybrid có he_so_khi_thai = 0.6
    → ma_tran kết quả = ma_tran_goc × 0.6
    
    ⚠️ HÀM NÀY PHẢI ĐƯỢC GỌI SAU KHI tao_ma_tran_od_bang_dijkstra() ĐÃ HOÀN THÀNH.
    """
    ma_tran_khi_thai_xe = ma_tran_khi_thai_goc * he_so_khi_thai_xe
    in_thong_bao(f"✔ Đã áp dụng hệ số loại xe: ×{he_so_khi_thai_xe} "
                 f"(Khí thải giảm {(1 - he_so_khi_thai_xe) * 100:.0f}%)")
    return ma_tran_khi_thai_xe
```

---

## 📄 File 6: `lop_3_vrp_solver/tabu_search_vrp.py`

```python
"""
=============================================================
LỚP 3: VRP SOLVER ENGINE — TABU SEARCH
Nhiệm vụ: Giải bài toán VRP multi-objective bằng Tabu Search
          tự xây dựng, KHÔNG dùng OR-Tools hay bất kỳ thư viện
          giải VRP nào.

NGUYÊN TẮC BẤT BIẾN:
  - Tabu Search CHỈ tra cứu 2 Ma trận OD tĩnh từ Lớp 2.
  - Tabu Search KHÔNG BAO GIỜ gọi đồ thị OSMnx hay Dijkstra.
  - Đây là mô phỏng chính xác cơ chế của ArcGIS VRP Solver.

CẤU TRÚC GIẢI THUẬT:
  ┌──────────────────────────────────────────────────┐
  │  1. Khởi tạo lộ trình ban đầu (Nearest Neighbor) │
  │  2. Vòng lặp Tabu Search (toi_da_vong_lap lần):  │
  │     a. Sinh tập hàng xóm (Relocate + Exchange)   │
  │     b. Đánh giá mỗi nước đi (tra ma trận OD)    │
  │     c. Kiểm tra Time Window (biến cộng dồn)      │
  │     d. Chọn nước đi tốt nhất không trong Tabu    │
  │     e. Cập nhật Tabu List                        │
  │     f. Cập nhật lời giải tốt nhất toàn cục      │
  └──────────────────────────────────────────────────┘
=============================================================
"""

import copy
import random
from typing import List, Tuple, Dict, Optional
import numpy as np
from giao_dien.terminal_ui import (in_tieu_de, in_thong_bao,
                                    in_canh_bao, in_tien_trinh, in_ket_qua)


# ─────────────────────────────────────────────────────────────
# KIỂU DỮ LIỆU TRUNG TÂM
# ─────────────────────────────────────────────────────────────
# Một "lộ trình" là list[int] — danh sách index khách hàng
# (không tính kho, kho luôn là điểm xuất phát & kết thúc)
# Ví dụ: [2, 5, 1] nghĩa là Kho → KH_2 → KH_5 → KH_1 → Kho

# Một "nước đi" (move) là tuple mô tả phép hoán đổi:
# ('relocate', xe_nguon, vi_tri_nguon, xe_dich, vi_tri_dich)
# ('exchange', xe_1, vi_tri_1, xe_2, vi_tri_2)

# ─────────────────────────────────────────────────────────────
# CLASS CHÍNH: TABU SEARCH VRP SOLVER
# ─────────────────────────────────────────────────────────────
class TabuSearchVRPSolver:
    """
    Tabu Search giải bài toán VRPTW (VRP + Time Windows) đa mục tiêu.
    Hoàn toàn tự xây dựng — không phụ thuộc thư viện VRP bên ngoài.
    """

    def __init__(self,
                 so_xe: int,
                 danh_sach_khach_hang: list,
                 cau_hinh_xe: list,
                 # ── 2 Ma trận OD tĩnh từ Lớp 2 (NGUỒN DỮ LIỆU DUY NHẤT) ──
                 ma_tran_chi_phi: np.ndarray,
                 ma_tran_khi_thai: np.ndarray,   # Đã nhân hệ số loại xe
                 ma_tran_thoi_gian_giay: np.ndarray,
                 # ── Tham số Tabu Search ──
                 toi_da_vong_lap: int = 500,
                 do_dai_tabu: int = 15,
                 trong_so_chi_phi: float = 0.5,  # α: trọng số chi phí tài chính
                 trong_so_khi_thai: float = 0.5  # β: trọng số khí thải
                 ):
        """
        Khởi tạo bộ giải.

        Tham số:
            danh_sach_khach_hang: list[dict], index 0 tương ứng KH đầu tiên
                                   (KHÔNG bao gồm kho — kho là index 0 trong ma trận)
            ma_tran_*: Ma trận N×N, index 0 = kho, index 1..N-1 = khách hàng
        """
        self.so_xe                    = so_xe
        self.khach_hang               = danh_sach_khach_hang
        self.so_khach_hang            = len(danh_sach_khach_hang)
        self.cau_hinh_xe              = cau_hinh_xe

        # ── Lưu trữ 2 Ma trận OD ── (đây là nguồn dữ liệu duy nhất)
        self.ma_tran_chi_phi            = ma_tran_chi_phi
        self.ma_tran_khi_thai           = ma_tran_khi_thai
        self.ma_tran_thoi_gian_giay     = ma_tran_thoi_gian_giay

        # ── Tham số Tabu ──
        self.toi_da_vong_lap            = toi_da_vong_lap
        self.do_dai_tabu                = do_dai_tabu
        self.trong_so_chi_phi           = trong_so_chi_phi
        self.trong_so_khi_thai          = trong_so_khi_thai

        # ── Tabu List: mảng lưu các nước đi đã thực hiện gần đây ──
        # Mỗi phần tử là tuple mô tả nước đi → không được lặp lại
        self.tabu_list: List[tuple] = []

        # ── Lời giải tốt nhất toàn cục ──
        self.lo_trinh_tot_nhat: Optional[List[List[int]]] = None
        self.chi_phi_tot_nhat: float = float("inf")
        self.khi_thai_tot_nhat: float = float("inf")
        self.ham_muc_tieu_tot_nhat: float = float("inf")

    # ═══════════════════════════════════════════════════════════
    # BƯỚC 1: KHỞI TẠO LỘ TRÌNH (NEAREST NEIGHBOR HEURISTIC)
    # ═══════════════════════════════════════════════════════════
    def _khoi_tao_lo_trinh_nearest_neighbor(self) -> List[List[int]]:
        """
        Xây dựng lộ trình ban đầu bằng heuristic Nearest Neighbor.
        Phân công khách hàng cho từng xe theo vòng tròn, ưu tiên gần nhất.

        Index khách hàng trong ma trận: 1-based (0 = kho).
        Index trong self.khach_hang:    0-based.
        → Khi tra ma trận: index_ma_tran = index_kh + 1
        """
        # Danh sách index khách hàng chưa được phân công (index 0-based)
        khach_chua_phan_cong = list(range(self.so_khach_hang))
        random.shuffle(khach_chua_phan_cong)  # Xáo trộn nhẹ để đa dạng hóa

        lo_trinh  = [[] for _ in range(self.so_xe)]  # Mỗi xe có 1 list khách hàng

        xe_hien_tai = 0
        vi_tri_hien_tai_mat_tran = 0  # Bắt đầu từ kho (index 0 trong ma trận)

        while khach_chua_phan_cong:
            # Tìm khách gần nhất (tốn thời gian đi ít nhất) theo ma trận OD
            kh_gan_nhat_idx = None
            thoi_gian_ngan_nhat = float("inf")

            for kh_idx in khach_chua_phan_cong:
                idx_ma_tran = kh_idx + 1  # +1 vì kho chiếm index 0
                tg = self.ma_tran_thoi_gian_giay[vi_tri_hien_tai_mat_tran][idx_ma_tran]
                if tg < thoi_gian_ngan_nhat:
                    thoi_gian_ngan_nhat = tg
                    kh_gan_nhat_idx = kh_idx

            # Phân công khách gần nhất cho xe hiện tại
            lo_trinh[xe_hien_tai].append(kh_gan_nhat_idx)
            khach_chua_phan_cong.remove(kh_gan_nhat_idx)
            vi_tri_hien_tai_mat_tran = kh_gan_nhat_idx + 1

            # Chuyển sang xe tiếp theo (luân phiên)
            xe_hien_tai = (xe_hien_tai + 1) % self.so_xe
            if xe_hien_tai == 0:
                vi_tri_hien_tai_mat_tran = 0  # Quay về kho

        return lo_trinh

    # ═══════════════════════════════════════════════════════════
    # BƯỚC 2A: ĐÁNH GIÁ MỘT LỘ TRÌNH (KIỂM TRA TIME WINDOW)
    # ═══════════════════════════════════════════════════════════
    def _danh_gia_mot_xe(self, lo_trinh_mot_xe: List[int]) -> Tuple[float, float, bool]:
        """
        Tính chi phí + khí thải cho MỘT xe, đồng thời kiểm tra Time Window.
        Tra cứu từ 2 Ma trận OD — KHÔNG gọi đồ thị.

        BIẾN CỘT LÕI: thoi_gian_hien_tai (phút)
        Công thức cộng dồn tại mỗi điểm:
            thoi_gian_hien_tai += thoi_gian_di_duong (tra ma trận)
            IF thoi_gian_hien_tai < thoi_gian_mo_cua:
                thoi_gian_hien_tai = thoi_gian_mo_cua  # Chờ mở cửa
            IF thoi_gian_hien_tai > thoi_gian_dong_cua:
                → INFEASIBLE (vi phạm time window cứng)
            thoi_gian_hien_tai += thoi_gian_boc_do

        Trả về:
            (chi_phi_usd, khi_thai_gram, la_hop_le)
        """
        if not lo_trinh_mot_xe:
            return 0.0, 0.0, True

        tong_chi_phi  = 0.0
        tong_khi_thai = 0.0
        la_hop_le     = True

        vi_tri_truoc_mat_tran = 0         # Bắt đầu từ kho (index 0 trong ma trận)
        thoi_gian_hien_tai    = 0.0       # Phút, tính từ đầu ca (0h00 hoặc giờ bắt đầu)

        for kh_idx in lo_trinh_mot_xe:
            idx_ma_tran = kh_idx + 1      # Chuyển sang index ma trận (+1 vì kho = 0)
            khach = self.khach_hang[kh_idx]

            # ── Tra ma trận: thời gian đi đường (giây → phút) ──
            thoi_gian_di_duong_giay = self.ma_tran_thoi_gian_giay[vi_tri_truoc_mat_tran][idx_ma_tran]
            thoi_gian_di_duong_phut = thoi_gian_di_duong_giay / 60.0

            # ── Tra ma trận: chi phí và khí thải ──
            chi_phi_canh   = self.ma_tran_chi_phi[vi_tri_truoc_mat_tran][idx_ma_tran]
            khi_thai_canh  = self.ma_tran_khi_thai[vi_tri_truoc_mat_tran][idx_ma_tran]

            if chi_phi_canh == float("inf") or khi_thai_canh == float("inf"):
                return float("inf"), float("inf"), False

            tong_chi_phi  += chi_phi_canh
            tong_khi_thai += khi_thai_canh

            # ── Cộng dồn thời gian ──
            thoi_gian_hien_tai += thoi_gian_di_duong_phut

            # ── Kiểm tra Time Window (cứng) ──
            thoi_gian_mo_cua  = khach["thoi_gian_mo_cua"]
            thoi_gian_dong_cua = khach["thoi_gian_dong_cua"]
            thoi_gian_boc_do  = khach["thoi_gian_boc_do"]

            # Nếu đến sớm → chờ
            if thoi_gian_hien_tai < thoi_gian_mo_cua:
                thoi_gian_hien_tai = thoi_gian_mo_cua

            # Nếu đến muộn → INFEASIBLE → loại bỏ ngay
            if thoi_gian_hien_tai > thoi_gian_dong_cua:
                la_hop_le = False
                return float("inf"), float("inf"), False

            # Cộng thêm thời gian bốc/dỡ
            thoi_gian_hien_tai += thoi_gian_boc_do

            vi_tri_truoc_mat_tran = idx_ma_tran

        # ── Chi phí đoạn về kho ──
        chi_phi_ve_kho  = self.ma_tran_chi_phi[vi_tri_truoc_mat_tran][0]
        khi_thai_ve_kho = self.ma_tran_khi_thai[vi_tri_truoc_mat_tran][0]
        tong_chi_phi  += chi_phi_ve_kho
        tong_khi_thai += khi_thai_ve_kho

        return tong_chi_phi, tong_khi_thai, la_hop_le

    # ═══════════════════════════════════════════════════════════
    # BƯỚC 2B: HÀM MỤC TIÊU (COST FUNCTION)
    # Đánh giá toàn bộ đội xe — dùng để so sánh giữa các vòng lặp
    # ═══════════════════════════════════════════════════════════
    def _ham_muc_tieu(self, lo_trinh: List[List[int]]) -> Tuple[float, float, float, bool]:
        """
        Tính tổng hàm mục tiêu đa mục tiêu cho TOÀN ĐỘI XE.
        Công thức: F = α × (Chi phí chuẩn hóa) + β × (Khí thải chuẩn hóa)

        Trả về:
            (ham_muc_tieu, tong_chi_phi, tong_khi_thai, la_hop_le)
        """
        tong_chi_phi  = 0.0
        tong_khi_thai = 0.0
        la_hop_le     = True

        for lo_trinh_mot_xe in lo_trinh:
            cp, kt, hop_le = self._danh_gia_mot_xe(lo_trinh_mot_xe)
            if not hop_le:
                return float("inf"), float("inf"), float("inf"), False
            tong_chi_phi  += cp
            tong_khi_thai += kt

        # Hàm mục tiêu tuyến tính có trọng số
        # (Đơn giản hóa: dùng sum có trọng số, không chuẩn hóa riêng lẻ)
        ham_muc_tieu = (self.trong_so_chi_phi * tong_chi_phi +
                        self.trong_so_khi_thai * tong_khi_thai)

        return ham_muc_tieu, tong_chi_phi, tong_khi_thai, True

    # ═══════════════════════════════════════════════════════════
    # BƯỚC 3A: INTER-ROUTE MOVE — RELOCATE
    # Rút khách hàng từ Xe_nguon, cắm vào Xe_dich
    # ═══════════════════════════════════════════════════════════
    def _sinh_nuoc_di_relocate(self,
                                lo_trinh: List[List[int]]
                                ) -> List[Tuple]:
        """
        Sinh danh sách tất cả nước đi Relocate hợp lệ.
        RELOCATE: Chuyển KH[xe_nguon][vt_nguon] → chèn vào xe_dich tại vt_dich.

        Trả về:
            list of (loai_nuoc_di, xe_nguon, vt_nguon, xe_dich, vt_dich, lo_trinh_moi)
        """
        tat_ca_nuoc_di = []

        for xe_nguon in range(self.so_xe):
            if not lo_trinh[xe_nguon]:
                continue

            for vt_nguon, kh_chuyen in enumerate(lo_trinh[xe_nguon]):
                # Thử chèn vào TẤT CẢ vị trí của tất cả xe KHÁC
                for xe_dich in range(self.so_xe):
                    if xe_nguon == xe_dich:
                        continue

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
        Sinh danh sách tất cả nước đi Exchange hợp lệ.
        EXCHANGE: Đổi vị trí KH[xe_1][vt_1] ↔ KH[xe_2][vt_2] (2 xe khác nhau).

        Trả về:
            list of (loai_nuoc_di, xe_1, vt_1, xe_2, vt_2, lo_trinh_moi)
        """
        tat_ca_nuoc_di = []

        for xe_1 in range(self.so_xe):
            if not lo_trinh[xe_1]:
                continue

            for xe_2 in range(xe_1 + 1, self.so_xe):  # Chỉ xét cặp (xe_1 < xe_2) tránh trùng
                if not lo_trinh[xe_2]:
                    continue

                for vt_1, kh_1 in enumerate(lo_trinh[xe_1]):
                    for vt_2, kh_2 in enumerate(lo_trinh[xe_2]):
                        # Tạo bản sao và thực hiện đổi chéo
                        lo_trinh_moi = copy.deepcopy(lo_trinh)
                        lo_trinh_moi[xe_1][vt_1] = kh_2
                        lo_trinh_moi[xe_2][vt_2] = kh_1

                        nuoc_di = ("exchange", xe_1, vt_1, xe_2, vt_2)
                        tat_ca_nuoc_di.append((nuoc_di, lo_trinh_moi))

        return tat_ca_nuoc_di

    # ═══════════════════════════════════════════════════════════
    # BƯỚC 4: KIỂM TRA TABU LIST + TIÊU CHÍ ASPIRATION
    # ═══════════════════════════════════════════════════════════
    def _la_tabu(self, nuoc_di: tuple) -> bool:
        """Kiểm tra xem nước đi có trong Tabu List hiện tại không."""
        return nuoc_di in self.tabu_list

    def _them_vao_tabu(self, nuoc_di: tuple):
        """
        Thêm nước đi vào Tabu List.
        Nếu vượt độ dài tối đa → xóa phần tử cũ nhất (FIFO).
        """
        self.tabu_list.append(nuoc_di)
        if len(self.tabu_list) > self.do_dai_tabu:
            self.tabu_list.pop(0)  # Xóa nước đi cũ nhất

    # ═══════════════════════════════════════════════════════════
    # VÒNG LẶP CHÍNH: TABU SEARCH
    # ═══════════════════════════════════════════════════════════
    def giai(self) -> Dict:
        """
        Hàm chính: Khởi động Tabu Search và trả về lời giải tốt nhất.

        LUỒNG XỬ LÝ:
        1. Khởi tạo lộ trình ban đầu
        2. Lặp toi_da_vong_lap lần:
           a. Sinh tập hàng xóm = Relocate ∪ Exchange
           b. Đánh giá từng nước đi (tra ma trận OD)
           c. Chọn nước đi tốt nhất thỏa điều kiện (không tabu HOẶC aspiration)
           d. Cập nhật Tabu List
           e. Cập nhật best solution
        3. Trả về kết quả
        """
        in_tieu_de("LỚP 3: VRP SOLVER — TABU SEARCH")
        in_thong_bao(f"Số vòng lặp tối đa: {self.toi_da_vong_lap}")
        in_thong_bao(f"Độ dài Tabu List:   {self.do_dai_tabu}")
        in_thong_bao(f"Trọng số α (chi phí): {self.trong_so_chi_phi} | "
                     f"β (khí thải): {self.trong_so_khi_thai}")

        # ── Bước 1: Khởi tạo lộ trình ban đầu ──
        lo_trinh_hien_tai = self._khoi_tao_lo_trinh_nearest_neighbor()
        f_hien_tai, cp_hien_tai, kt_hien_tai, _ = self._ham_muc_tieu(lo_trinh_hien_tai)

        # Cập nhật best solution ban đầu
        self.lo_trinh_tot_nhat       = copy.deepcopy(lo_trinh_hien_tai)
        self.ham_muc_tieu_tot_nhat   = f_hien_tai
        self.chi_phi_tot_nhat        = cp_hien_tai
        self.khi_thai_tot_nhat       = kt_hien_tai

        in_thong_bao(f"Lộ trình ban đầu — F={f_hien_tai:.4f} "
                     f"(CP=${cp_hien_tai:.2f}, KT={kt_hien_tai:.1f}g)")

        # ── Bước 2: Vòng lặp Tabu Search ──
        for vong_lap in range(self.toi_da_vong_lap):

            # a. Sinh tập hàng xóm
            tat_ca_nuoc_di = (self._sinh_nuoc_di_relocate(lo_trinh_hien_tai) +
                              self._sinh_nuoc_di_exchange(lo_trinh_hien_tai))

            if not tat_ca_nuoc_di:
                in_canh_bao(f"  Không còn nước đi hợp lệ tại vòng {vong_lap}. Dừng sớm.")
                break

            # b. Đánh giá từng nước đi và chọn ứng viên tốt nhất
            nuoc_di_chon    = None
            lo_trinh_chon   = None
            f_chon          = float("inf")
            cp_chon         = float("inf")
            kt_chon         = float("inf")

            for nuoc_di, lo_trinh_ung_vien in tat_ca_nuoc_di:

                f_uv, cp_uv, kt_uv, hop_le = self._ham_muc_tieu(lo_trinh_ung_vien)

                if not hop_le:
                    continue  # Bỏ qua lộ trình vi phạm time window

                # c. Kiểm tra điều kiện chọn:
                #    - Không trong Tabu List, HOẶC
                #    - Trong Tabu nhưng tốt hơn best toàn cục (Aspiration Criterion)
                la_tabu = self._la_tabu(nuoc_di)
                vuot_qua_aspiration = (f_uv < self.ham_muc_tieu_tot_nhat)

                if (not la_tabu or vuot_qua_aspiration) and f_uv < f_chon:
                    nuoc_di_chon  = nuoc_di
                    lo_trinh_chon = lo_trinh_ung_vien
                    f_chon  = f_uv
                    cp_chon = cp_uv
                    kt_chon = kt_uv

            if nuoc_di_chon is None:
                in_canh_bao(f"  Tất cả nước đi đều bị Tabu tại vòng {vong_lap}.")
                continue

            # d. Cập nhật trạng thái hiện tại
            lo_trinh_hien_tai = lo_trinh_chon
            f_hien_tai        = f_chon

            # d. Thêm nước đi vào Tabu List
            self._them_vao_tabu(nuoc_di_chon)

            # e. Cập nhật best solution nếu tốt hơn
            if f_chon < self.ham_muc_tieu_tot_nhat:
                self.lo_trinh_tot_nhat     = copy.deepcopy(lo_trinh_chon)
                self.ham_muc_tieu_tot_nhat = f_chon
                self.chi_phi_tot_nhat      = cp_chon
                self.khi_thai_tot_nhat     = kt_chon
                in_thong_bao(f"  ✨ Vòng {vong_lap:4d}: Cải thiện! "
                             f"F={f_chon:.4f} (CP=${cp_chon:.2f}, KT={kt_chon:.1f}g) "
                             f"[{nuoc_di_chon[0].upper()}]")

            # Hiển thị tiến trình
            if vong_lap % max(1, self.toi_da_vong_lap // 20) == 0:
                in_tien_trinh(vong_lap / self.toi_da_vong_lap * 100,
                              f"Tabu Search: vòng {vong_lap}/{self.toi_da_vong_lap}")

        in_thong_bao("✔ Tabu Search hoàn thành.")
        return self._xuat_ket_qua()

    # ═══════════════════════════════════════════════════════════
    # XUẤT KẾT QUẢ
    # ═══════════════════════════════════════════════════════════
    def _xuat_ket_qua(self) -> Dict:
        """Đóng gói và trả về kết quả dưới dạng dict."""
        ket_qua = {
            "ham_muc_tieu":  self.ham_muc_tieu_tot_nhat,
            "tong_chi_phi":  self.chi_phi_tot_nhat,
            "tong_khi_thai": self.khi_thai_tot_nhat,
            "lo_trinh":      {}
        }

        in_ket_qua("═══ KẾT QUẢ LỘ TRÌNH TỐT NHẤT ═══")
        in_ket_qua(f"Hàm mục tiêu F = {self.ham_muc_tieu_tot_nhat:.4f}")
        in_ket_qua(f"Tổng chi phí  = ${self.chi_phi_tot_nhat:.2f}")
        in_ket_qua(f"Tổng khí thải = {self.khi_thai_tot_nhat:.1f} gram CO2")

        for xe_idx, lo_trinh_mot_xe in enumerate(self.lo_trinh_tot_nhat):
            ten_xe = self.cau_hinh_xe[xe_idx]["ma_xe"] if xe_idx < len(self.cau_hinh_xe) else f"XE_{xe_idx}"
            loai_xe = self.cau_hinh_xe[xe_idx]["loai_xe"] if xe_idx < len(self.cau_hinh_xe) else "N/A"

            ten_cac_kh = [self.khach_hang[kh]["ten"] for kh in lo_trinh_mot_xe]
            mo_ta_lo_trinh = " → ".join(["Kho"] + ten_cac_kh + ["Kho"])

            cp_xe, kt_xe, _ = self._danh_gia_mot_xe(lo_trinh_mot_xe)
            ket_qua["lo_trinh"][ten_xe] = {
                "loai_xe":    loai_xe,
                "lo_trinh":   lo_trinh_mot_xe,
                "mo_ta":      mo_ta_lo_trinh,
                "chi_phi":    cp_xe,
                "khi_thai":   kt_xe
            }

            in_ket_qua(f"\n  [{ten_xe} — {loai_xe}]")
            in_ket_qua(f"  Lộ trình: {mo_ta_lo_trinh}")
            in_ket_qua(f"  Chi phí: ${cp_xe:.2f} | Khí thải: {kt_xe:.1f}g CO2")

        return ket_qua
```

---

## 📄 File 7: `giao_dien/terminal_ui.py`

```python
"""
=============================================================
GIAO DIỆN TERMINAL — MINIMALIST BLUE PASTEL THEME
Thiết kế: Màu xanh dương nhạt (ANSI escape codes)
=============================================================
"""

import sys


# ─────────────────────────────────────────────────────────────
# BẢN MÀU ANSI — BLUE/LIGHT PASTEL THEME
# ─────────────────────────────────────────────────────────────
class Mau:
    RESET        = "\033[0m"
    # Xanh dương nhạt (pastel)
    XANH_NHAT   = "\033[94m"   # Bright Blue — dùng cho tiêu đề
    XANH_DUONG  = "\033[34m"   # Standard Blue — dùng cho thông báo
    XANH_LUC    = "\033[92m"   # Bright Green — dùng cho kết quả tốt
    VANG        = "\033[93m"   # Yellow — dùng cho cảnh báo
    DO          = "\033[91m"   # Red — dùng cho lỗi
    TRANG_NHAT  = "\033[97m"   # Bright White — dùng cho text chính
    XAM         = "\033[90m"   # Gray — dùng cho phụ
    DAM         = "\033[1m"    # Bold
    GAch_CHAN   = "\033[4m"    # Underline


# ─────────────────────────────────────────────────────────────
# HÀM IN CÁC LOẠI THÔNG BÁO
# ─────────────────────────────────────────────────────────────
def in_tieu_de(noi_dung: str):
    """In tiêu đề lớn theo phong cách ArcGIS-inspired."""
    chieu_rong = 60
    duong_ke   = "═" * chieu_rong
    print(f"\n{Mau.XANH_NHAT}{Mau.DAM}{duong_ke}{Mau.RESET}")
    print(f"{Mau.XANH_NHAT}{Mau.DAM}  {noi_dung.center(chieu_rong - 2)}{Mau.RESET}")
    print(f"{Mau.XANH_NHAT}{Mau.DAM}{duong_ke}{Mau.RESET}")


def in_thong_bao(noi_dung: str):
    """In thông báo thông thường màu xanh nhạt."""
    print(f"{Mau.XANH_DUONG}  {noi_dung}{Mau.RESET}")


def in_canh_bao(noi_dung: str):
    """In cảnh báo màu vàng."""
    print(f"{Mau.VANG}  ⚠ {noi_dung}{Mau.RESET}")


def in_loi(noi_dung: str):
    """In thông báo lỗi màu đỏ."""
    print(f"{Mau.DO}  ✗ LỖI: {noi_dung}{Mau.RESET}")


def in_ket_qua(noi_dung: str):
    """In kết quả quan trọng màu xanh lục."""
    print(f"{Mau.XANH_LUC}{Mau.DAM}  {noi_dung}{Mau.RESET}")


def in_tien_trinh(phan_tram: float, mo_ta: str = ""):
    """In thanh tiến trình trực quan."""
    chieu_dai_thanh = 30
    so_o_day = int(phan_tram / 100 * chieu_dai_thanh)
    thanh = "█" * so_o_day + "░" * (chieu_dai_thanh - so_o_day)
    sys.stdout.write(
        f"\r{Mau.XANH_NHAT}  [{thanh}] {phan_tram:5.1f}%  {mo_ta}{Mau.RESET}"
    )
    sys.stdout.flush()
    if phan_tram >= 100:
        print()  # Xuống dòng khi hoàn thành


def in_duong_ngang():
    """In đường kẻ ngang phân chia."""
    print(f"{Mau.XAM}  {'─' * 56}{Mau.RESET}")


def in_banner():
    """In banner khởi động hệ thống."""
    print(f"""
{Mau.XANH_NHAT}{Mau.DAM}
  ╔══════════════════════════════════════════════════════╗
  ║     CITY VRP — ArcGIS Network Analyst Clone         ║
  ║     Kiến trúc 3 Lớp: Dijkstra → Tabu Search        ║
  ║     Phiên bản: 1.0 | Ngôn ngữ: Python + OSMnx      ║
  ╚══════════════════════════════════════════════════════╝
{Mau.RESET}""")
```

---

## 📄 File 8: `main.py` — Điểm Điều Phối Trung Tâm

```python
"""
=============================================================
MAIN.PY — ĐIỂM KHỞI ĐỘNG HỆ THỐNG
Điều phối 3 lớp theo đúng thứ tự kiến trúc ArcGIS:

  LỚP 1 → LỚP 2 (Dijkstra) → [Nhân hệ số xe] → LỚP 3 (Tabu)

LUỒNG DỮ LIỆU:
  JSON Files
    └→ [Lớp 1] Tiền xử lý → dict Python
         └→ [Lớp 2] Dijkstra → Ma trận OD gốc
              └→ [Ngoài Dijkstra] Nhân hệ số xe → Ma trận OD theo xe
                   └→ [Lớp 3] Tabu Search → Lộ trình tối ưu
=============================================================
"""

import json
import os
import numpy as np

# ── Import 3 lớp ──
from lop_1_tien_xu_ly.tao_du_lieu         import tai_va_xu_ly_du_lieu
from lop_2_network_analyst.dijkstra_ma_tran_od import (
    tai_do_thi_duong_pho,
    snap_diem_vao_do_thi,
    tao_ma_tran_od_bang_dijkstra,
    ap_dung_he_so_loai_xe          # Hàm nhân hệ số — gọi SAU Dijkstra
)
from lop_3_vrp_solver.tabu_search_vrp     import TabuSearchVRPSolver
from giao_dien.terminal_ui                import (
    in_banner, in_tieu_de, in_thong_bao, in_ket_qua, in_canh_bao
)


# ─────────────────────────────────────────────────────────────
# CẤU HÌNH CHẠY HỆ THỐNG
# ─────────────────────────────────────────────────────────────
CAU_HINH_CHAY = {
    "thu_muc_du_lieu":   "du_lieu",
    "ten_thanh_pho_osm": "Ho Chi Minh City, Vietnam",
    "ban_kinh_ban_do_m": 8000,       # Bán kính tải bản đồ (mét)
    "ma_xe_giai":        "XE_02",    # Chọn xe để giải (ảnh hưởng hệ số khí thải)
    "tham_so_tabu": {
        "toi_da_vong_lap": 300,
        "do_dai_tabu":     12,
        "trong_so_chi_phi":  0.5,    # α
        "trong_so_khi_thai": 0.5     # β
    },
    "luu_ket_qua_json":   True,
    "file_ket_qua":       "ket_qua_vrp.json"
}


# ─────────────────────────────────────────────────────────────
# HÀM CHÍNH
# ─────────────────────────────────────────────────────────────
def chay_he_thong():
    """
    Hàm điều phối trung tâm — chạy 3 lớp theo đúng thứ tự.
    """
    in_banner()

    # ══════════════════════════════════════════════════════════
    # BƯỚC 1: LỚP 1 — TIỀN XỬ LÝ DỮ LIỆU
    # ══════════════════════════════════════════════════════════
    du_lieu = tai_va_xu_ly_du_lieu(CAU_HINH_CHAY["thu_muc_du_lieu"])

    bang_moves      = du_lieu["bang_moves"]
    tat_ca_diem     = du_lieu["tat_ca_diem"]      # index 0 = kho
    danh_sach_kh    = du_lieu["khach_hang"]       # index 0 = KH đầu tiên
    danh_sach_xe    = du_lieu["cau_hinh_xe"]
    luong_tai_xe    = du_lieu["luong_tai_xe"]

    # Tìm cấu hình xe được chọn để giải
    ma_xe_chon = CAU_HINH_CHAY["ma_xe_giai"]
    cau_hinh_xe_chon = next(
        (xe for xe in danh_sach_xe if xe["ma_xe"] == ma_xe_chon),
        danh_sach_xe[0]  # fallback về xe đầu tiên
    )
    he_so_khi_thai_xe = cau_hinh_xe_chon["he_so_khi_thai"]

    in_thong_bao(f"Xe được chọn giải: {ma_xe_chon} "
                 f"({cau_hinh_xe_chon['loai_xe']}, "
                 f"hệ số khí thải: ×{he_so_khi_thai_xe})")

    # ══════════════════════════════════════════════════════════
    # BƯỚC 2: LỚP 2 — NETWORK ANALYST (DIJKSTRA)
    # ══════════════════════════════════════════════════════════

    # 2.1: Tải đồ thị đường phố
    do_thi = tai_do_thi_duong_pho(
        ten_thanh_pho=CAU_HINH_CHAY["ten_thanh_pho_osm"],
        ban_kinh_met=CAU_HINH_CHAY["ban_kinh_ban_do_m"]
    )

    # 2.2: Snap các điểm vào đồ thị
    danh_sach_node_osm = snap_diem_vao_do_thi(do_thi, tat_ca_diem)

    # 2.3: Chạy Dijkstra → 4 ma trận gốc (Dijkstra chạy XONG HOÀN TOÀN)
    (ma_tran_chi_phi,
     ma_tran_khi_thai_goc,      # ← Chưa nhân hệ số xe
     ma_tran_thoi_gian_giay,
     ma_tran_quang_duong_km) = tao_ma_tran_od_bang_dijkstra(
        do_thi=do_thi,
        danh_sach_node_osm=danh_sach_node_osm,
        cau_hinh_xe=cau_hinh_xe_chon,
        luong_tai_xe_usd_per_gio=luong_tai_xe,
        bang_moves=bang_moves
    )

    # ══════════════════════════════════════════════════════════
    # BƯỚC 2.4: NHÂN HỆ SỐ LOẠI XE (SAU KHI DIJKSTRA XONG)
    # ← ĐÂY LÀ ĐIỂM MẤU CHỐT: nằm NGOÀI vòng lặp Dijkstra
    # ══════════════════════════════════════════════════════════
    in_tieu_de("ÁP DỤNG HỆ SỐ LOẠI XE VÀO MA TRẬN")
    ma_tran_khi_thai_xe = ap_dung_he_so_loai_xe(
        ma_tran_khi_thai_goc=ma_tran_khi_thai_goc,
        he_so_khi_thai_xe=he_so_khi_thai_xe
    )

    # ══════════════════════════════════════════════════════════
    # BƯỚC 3: LỚP 3 — VRP SOLVER (TABU SEARCH)
    # Tabu Search chỉ nhận 2 ma trận OD — không biết đến đồ thị
    # ══════════════════════════════════════════════════════════
    tham_so_tabu = CAU_HINH_CHAY["tham_so_tabu"]

    bo_giai = TabuSearchVRPSolver(
        so_xe=len(danh_sach_xe),
        danh_sach_khach_hang=danh_sach_kh,
        cau_hinh_xe=danh_sach_xe,
        ma_tran_chi_phi=ma_tran_chi_phi,
        ma_tran_khi_thai=ma_tran_khi_thai_xe,    # ← Ma trận đã nhân hệ số xe
        ma_tran_thoi_gian_giay=ma_tran_thoi_gian_giay,
        toi_da_vong_lap=tham_so_tabu["toi_da_vong_lap"],
        do_dai_tabu=tham_so_tabu["do_dai_tabu"],
        trong_so_chi_phi=tham_so_tabu["trong_so_chi_phi"],
        trong_so_khi_thai=tham_so_tabu["trong_so_khi_thai"]
    )

    ket_qua = bo_giai.giai()

    # ══════════════════════════════════════════════════════════
    # BƯỚC 4: LƯU KẾT QUẢ
    # ══════════════════════════════════════════════════════════
    if CAU_HINH_CHAY["luu_ket_qua_json"]:
        file_ket_qua = CAU_HINH_CHAY["file_ket_qua"]
        # Chuyển numpy array sang list để JSON serialize được
        ket_qua_luu = {
            "ham_muc_tieu":  float(ket_qua["ham_muc_tieu"]),
            "tong_chi_phi":  float(ket_qua["tong_chi_phi"]),
            "tong_khi_thai": float(ket_qua["tong_khi_thai"]),
            "lo_trinh":      {
                xe: {
                    k: (float(v) if isinstance(v, (np.floating, float)) else v)
                    for k, v in info.items()
                }
                for xe, info in ket_qua["lo_trinh"].items()
            }
        }
        with open(file_ket_qua, "w", encoding="utf-8") as f:
            json.dump(ket_qua_luu, f, ensure_ascii=False, indent=2)
        in_ket_qua(f"\n✔ Kết quả đã lưu vào: {file_ket_qua}")

    in_tieu_de("HỆ THỐNG HOÀN THÀNH")


# ─────────────────────────────────────────────────────────────
# ĐIỂM KHỞI CHẠY
# ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    chay_he_thong()
```

---

## 📄 File 9: `requirements.txt`

```text
# Thư viện cốt lõi
networkx>=3.0        # Dijkstra và đồ thị
osmnx>=1.6.0         # Tải bản đồ OSM
numpy>=1.24.0        # Ma trận OD

# Tiện ích
requests>=2.28.0     # osmnx phụ thuộc
shapely>=2.0.0       # osmnx phụ thuộc
```

---

## 📄 File 10: `__init__.py` (rỗng — để Python nhận diện package)

Tạo file rỗng tại:
- `lop_1_tien_xu_ly/__init__.py`
- `lop_2_network_analyst/__init__.py`
- `lop_3_vrp_solver/__init__.py`
- `giao_dien/__init__.py`

---

## 🚀 Hướng Dẫn Cài Đặt & Chạy

```bash
# 1. Cài đặt thư viện
pip install -r requirements.txt

# 2. Chạy hệ thống
python main.py
```

---

## 🏗️ Giải Thích Kiến Trúc — Tại Sao Thiết Kế Như Vậy?

### Sơ đồ luồng dữ liệu
```
[JSON Files]
     │
     ▼ Lớp 1: Đọc & xác thực
[dict Python: bang_moves, cau_hinh_xe, khach_hang]
     │
     ▼ Lớp 2: Dijkstra (chạy 1 lần duy nhất)
[OSMnx Graph] ──Dijkstra──▶ [ma_tran_chi_phi N×N]    (USD)
                         ──▶ [ma_tran_khi_thai_goc N×N] (g CO2, chưa nhân hệ số)
                         ──▶ [ma_tran_thoi_gian N×N]  (giây)
     │
     ▼ NGOÀI vòng lặp Dijkstra:
[ma_tran_khi_thai_goc × he_so_xe] = [ma_tran_khi_thai_xe]
     │
     ▼ Lớp 3: Tabu Search (chỉ đọc 2 ma trận)
[TabuSearchVRPSolver] ──tra ma_tran──▶ [Lộ trình tối ưu]
     │
     ▼
[ket_qua_vrp.json]
```

### Tại sao `ap_dung_he_so_loai_xe()` nằm NGOÀI Dijkstra?

**Đây là điểm mấu chốt về kiến trúc:**

| Cách Sai ❌ | Cách Đúng ✅ |
|---|---|
| Nhân hệ số xe TRONG vòng lặp `for i, for j` | Dijkstra chạy xong hoàn toàn, LẤY ma trận gốc |
| Mỗi lần tính cạnh đã nhân hệ số | Sau đó nhân một lần bằng numpy broadcasting |
| Nếu đổi xe phải chạy Dijkstra lại từ đầu | Ma trận gốc như "template", chỉ nhân khác nhau |

Điều này khớp với cơ chế ArcGIS: đồ thị đường phố **không biết** xe nào đang đi — đó là dữ liệu thuần hạ tầng. Chỉ sau khi xuất ma trận, bạn mới áp dụng đặc tính xe.

---

*Tài liệu này tạo ra bởi City VRP ArcGIS Clone System v1.0*
