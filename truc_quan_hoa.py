import pandas as pd
import matplotlib.pyplot as plt
import os

# Đường dẫn đến file dữ liệu
FILE_DATA = "city_vrp_arcgis/du_lieu/lich_su_chay.csv"

def ve_do_thi_so_sanh():
    if not os.path.exists(FILE_DATA):
        print(f"Lỗi: Không tìm thấy file dữ liệu tại {FILE_DATA}")
        return

    # Đọc dữ liệu
    df = pd.read_csv(FILE_DATA)
    if df.empty:
        print("Dữ liệu trống!")
        return

    # Tạo khu vực vẽ đồ thị duy nhất
    fig, ax1 = plt.subplots(figsize=(12, 6))

    # Đồ thị 1: Chi phí tài chính (Trục Y bên trái)
    color1 = 'royalblue'
    ax1.set_xlabel("Số thứ tự lần chạy (Index)")
    ax1.set_ylabel("Chi phí ($)", color=color1, fontweight='bold')
    lns1 = ax1.plot(df.index, df['Chi_Phi'], marker='o', color=color1, label='Chi phí ($)')
    ax1.tick_params(axis='y', labelcolor=color1)
    ax1.grid(True, linestyle='--', alpha=0.5)

    # Tạo trục Y thứ hai cho Khí thải
    ax2 = ax1.twinx()
    color2 = 'forestgreen'
    ax2.set_ylabel("Khí thải (g/CO2)", color=color2, fontweight='bold')
    lns2 = ax2.plot(df.index, df['Khi_Thai'], marker='s', color=color2, label='Khí thải (g/CO2)')
    ax2.tick_params(axis='y', labelcolor=color2)

    # Thu gom legend từ cả 2 trục để hiện chung 1 bảng
    lns = lns1 + lns2
    labs = [l.get_label() for l in lns]
    ax1.legend(lns, labs, loc='upper left')

    plt.title("So sánh tương quan giữa Chi phí và Khí thải qua các lần mô phỏng", fontsize=14, pad=20)
    fig.tight_layout()

    print("--- Thống kê nhanh ---")
    print(df[['Thoi_Gian', 'Chi_Phi', 'Khi_Thai']].tail())
    
    plt.show()

if __name__ == "__main__":
    ve_do_thi_so_sanh()
