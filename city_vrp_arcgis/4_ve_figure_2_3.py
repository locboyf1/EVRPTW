import os
import sys
import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# Xác định thư mục gốc dựa trên vị trí file này
_THU_MUC_GOC = os.path.dirname(os.path.abspath(__file__))
if _THU_MUC_GOC not in sys.path:
    sys.path.insert(0, _THU_MUC_GOC)

from giao_dien.terminal_ui import in_tieu_de

def main():
    in_tieu_de("PHASE 3: VẼ BIỂU ĐỒ (Wygonik & Goodchild)")
    
    # Đường dẫn tuyệt đối
    json_file = os.path.join(_THU_MUC_GOC, "ket_qua", "tabu_ket_qua.json")
    kh_file = os.path.join(_THU_MUC_GOC, "du_lieu", "khach_hang.json")
    csv_file = os.path.join(_THU_MUC_GOC, "ket_qua", "lich_su_so_sanh.csv")
    out_dir = os.path.join(_THU_MUC_GOC, "ket_qua")

    if not all(os.path.exists(f) for f in [json_file, kh_file, csv_file]):
        print("Lỗi: Thiếu file kết quả. Hãy chạy các bước trước.")
        return

    with open(json_file, "r", encoding="utf-8") as f:
        ket_qua = json.load(f)
    with open(kh_file, "r", encoding="utf-8") as f:
        kh_data = json.load(f)
    df_history = pd.read_csv(csv_file)

    # 1. Figure 2: Route Map
    plt.figure(figsize=(10, 8))
    # Vẽ khách hàng
    kho = kh_data["kho_xuat_phat"]
    plt.scatter(kho["kinh_do"], kho["vi_do"], c='red', marker='s', s=100, label="Kho")
    
    khach_hang = kh_data["danh_sach_khach_hang"]
    for kh in khach_hang:
        plt.scatter(kh["kinh_do"], kh["vi_do"], c='blue', alpha=0.5)
        plt.text(kh["kinh_do"], kh["vi_do"], kh["ten"], fontsize=8)

    # Vẽ lộ trình
    colors = plt.cm.rainbow(np.linspace(0, 1, len(ket_qua["lo_trinh"])))
    for (xe_id, data), color in zip(ket_qua["lo_trinh"].items(), colors):
        path_idx = data["thu_tu"]
        coords = [(kho["kinh_do"], kho["vi_do"])]
        for idx in path_idx:
            coords.append((khach_hang[idx]["kinh_do"], khach_hang[idx]["vi_do"]))
        coords.append((kho["kinh_do"], kho["vi_do"]))
        
        x, y = zip(*coords)
        plt.plot(x, y, c=color, alpha=0.7, linewidth=1.5)

    plt.title("Figure 2: EVRPTW Route Map (Vinh City)")
    plt.xlabel("Longitude")
    plt.ylabel("Latitude")
    plt.legend()
    plt.grid(True)
    fig2_path = os.path.join(out_dir, "figure_2_routes.png")
    plt.savefig(fig2_path)
    print(f"✔ Đã lưu Figure 2 vào {fig2_path}")

    # 2. Figure 3: Trade-off Curve (Pareto)
    fig, ax = plt.subplots(figsize=(8, 6))
    ax.scatter(df_history["Khi_Thai"], df_history["Chi_Phi"], c='darkgreen', s=100)
    
    # Annotate points
    for i, row in df_history.iterrows():
        ax.annotate(row["Kich_Ban"], (row["Khi_Thai"], row["Chi_Phi"]), 
                    xytext=(5, 5), textcoords='offset points', fontsize=9)

    ax.set_title("Figure 3: Trade-off Curve (Cost vs Emissions)")
    ax.set_xlabel("Emissions (g CO2)")
    ax.set_ylabel("Total Cost ($)")
    ax.grid(True, linestyle='--', alpha=0.6)
    
    # Dùng transAxes cho text ghi chú nếu cần
    ax.text(0.05, 0.95, "Lower-Left is Better", transform=ax.transAxes, 
            verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

    fig3_path = os.path.join(out_dir, "figure_3_tradeoff.png")
    plt.savefig(fig3_path)
    print(f"✔ Đã lưu Figure 3 vào {fig3_path}")
    plt.show()

if __name__ == "__main__":
    main()
