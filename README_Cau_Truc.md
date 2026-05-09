# V2 Mo Phong Wygonik — Kien Truc Modular & Plug-and-Play

> **Muc tieu**: Xay dung lai he thong VRP theo kien truc modular, san sang cho viec
> so sanh nhieu thuat toan meta-heuristic (Tabu Search, Ant Colony, GA...).
>
> **Nguyen tac cot loi**: Giao tiep qua FILE VAT LY (.npz), tuyet doi khong goi ham cheo.

---

## Cay Thu Muc

```
V2_Mo_Phong_Wygonik/
│
├── README_Cau_Truc.md          ← Ban dang doc file nay
│
├── cau_hinh/                   ← [1] CAU HINH TAP TRUNG
│   └── cau_hinh_co_so.json     ← Tat ca thong so he thong (so_xe, tai_trong,
│                                  gio_han_8h, time_window mode, kho, ...)
│
├── du_lieu_io/                 ← [2] SINH & XUAT DU LIEU
│   ├── 1b_sinh_khach_hang.py   ← Sinh N khach hang ngau nhien (Time Window mixed/fixed)
│   └── 2b_xuat_ma_tran_csv.py  ← Doc .npz → xuat .csv (header = ten KH, mo bang Excel)
│
├── loi_giai_mang_luoi/         ← [3] TANG MANG LUOI (Network Layer)
│   └── thuat_toan_dijkstra.py  ← Dijkstra: map → Ma_Tran_OD.npz
│                                  (Tuong lai: them thuat_toan_kien_doduong.py)
│
├── loi_giai_lo_trinh/          ← [4] TANG LO TRINH (Routing Layer)
│   └── thuat_toan_tabu.py      ← Tabu Search: load .npz → giai → ket_qua.json
│                                  (Tuong lai: them thuat_toan_aco.py, thuat_toan_ga.py)
│
├── khoi_chay/                  ← [5] DIEU PHOI PIPELINE
│   └── chay_kich_ban_goc.py    ← Ghep tat ca buoc theo thu tu: 1→2→3→4→5
│
├── bao_cao_ket_qua/            ← [6] BAO CAO KHOA HOC
│   ├── in_table_2_3.py         ← Xuat Table 2 (Chi phi) & Table 3 (Khi thai)
│   └── ve_figure_2_3.py        ← Ve Figure 2 (Route Map) & Figure 3 (Pareto)
│
├── giao_dien/                  ← [7] GIAO DIEN TERMINAL (doc lap)
│   └── terminal_ui.py          ← In mau, tieu de, tien trinh (self-contained)
│
└── du_lieu/                    ← [8] DU LIEU TRUNG GIAN
    ├── khach_hang.json          ← Output tu 1b_sinh_khach_hang.py
    ├── do_thi_osm.pkl           ← Cache ban do OSMnx
    ├── Ma_Tran_OD.npz           ← 4 ma tran (cp, kt, tg, km) — FILE GIAO TIEP CHINH
    ├── Ma_Tran_Chi_Phi.csv      ← CSV cho nguoi doc (Excel)
    ├── Ma_Tran_Thoi_Gian.csv
    ├── Ma_Tran_Khi_Thai.csv
    ├── Ma_Tran_Quang_Duong.csv
    ├── ket_qua_tabu.json        ← Lo trinh toi uu tu Tabu Search
    └── lich_su_so_sanh.csv      ← Log cac kich ban (phuc vu Table 2, 3)
```

---

## Luong Du Lieu (Pipeline)

```
cau_hinh_co_so.json
       │
       ▼
1b_sinh_khach_hang.py ──▶ khach_hang.json
       │
       ▼
thuat_toan_dijkstra.py ──▶ Ma_Tran_OD.npz  ← FILE GIAO TIEP VAT LY
       │
       ├──▶ 2b_xuat_ma_tran_csv.py ──▶ .csv (cho NGUOI doc)
       │
       ▼
thuat_toan_tabu.py ──▶ ket_qua_tabu.json   ← LOAD .npz, KHONG goi ham cheo
       │
       ▼
in_table_2_3.py / ve_figure_2_3.py ──▶ Bang & Bieu do
```

### Nguyen tac giao tiep

| Tang                  | Input                     | Output              |
|-----------------------|---------------------------|---------------------|
| loi_giai_mang_luoi/   | map + khach_hang.json     | Ma_Tran_OD.npz      |
| loi_giai_lo_trinh/    | Ma_Tran_OD.npz (LOAD)     | ket_qua_tabu.json   |

**Quy tac vang**: `loi_giai_mang_luoi/` va `loi_giai_lo_trinh/` KHONG BAO GIO import lan nhau.
Chung chi giao tiep qua file `Ma_Tran_OD.npz`.

---

## Time Window — 2 Che Do

| Che do   | Giai thich                                      | Kich ban bao cao |
|----------|-------------------------------------------------|------------------|
| `mixed`  | Random do rong 30-120 phut cho tung KH          | [a] Weighted Avg |
| `fixed`  | Tat ca KH cung do rong = `do_rong_cua_so_phut`  | [b] Fixed Width  |

Chuyen che do: sua `"che_do_time_window"` trong `cau_hinh_co_so.json`.

---

## Rang Buoc 8 Tieng

Trong `thuat_toan_tabu.py`, ham `_danh_gia_mot_xe()` kiem tra:

```
tong_thoi_gian (roi kho → giao hang → ve kho) <= gio_han_lam_viec_phut (480)
```

Neu vuot → lo trinh do bi danh dau INFEASIBLE va bi loai.

---

## Cach Them Thuat Toan Moi (Plug-and-Play)

1. **Them engine mang luoi**: Tao file moi trong `loi_giai_mang_luoi/`
   (vd: `thuat_toan_kien_doduong.py`). Output van la `Ma_Tran_OD.npz`.

2. **Them engine lo trinh**: Tao file moi trong `loi_giai_lo_trinh/`
   (vd: `thuat_toan_aco.py`). Input van la load `Ma_Tran_OD.npz`.

3. Chi can dam bao **interface file** giong nhau (4 key: cp, kt, tg, km).

---

*Tai lieu tao boi V2 Mo Phong Wygonik System v2.0*
