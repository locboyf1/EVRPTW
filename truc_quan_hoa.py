import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os

# Đường dẫn đến file dữ liệu
FILE_DATA = "city_vrp_arcgis/du_lieu/lich_su_chay.csv"

def tinh_hoi_quy_qua_goc_0(x, y):
    """
    Tính phương trình y = ax (bắt buộc đi qua điểm 0,0)
    Sử dụng giải thuật bình phương tối thiểu (Ordinary Least Squares)
    """
    x = np.array(x)
    y = np.array(y)
    
    # Tính hệ số góc a = sum(xy) / sum(x^2)
    a = np.sum(x * y) / np.sum(x**2)
    
    # Tính R-squared (hệ số xác định) cho mô hình đi qua gốc tọa độ
    # R2 = 1 - (Tổng bình phương sai số / Tổng bình phương giá trị thực tế)
    y_pred = a * x
    ss_res = np.sum((y - y_pred)**2)
    ss_tot = np.sum(y**2)
    r2 = 1 - (ss_res / ss_tot)
    
    return a, r2

def ve_do_thi_phan_tan_khoa_hoc():
    if not os.path.exists(FILE_DATA):
        print(f"Loi: Khong tim thay file du lieu tai {FILE_DATA}")
        return

    # 1. Đọc và Tiền xử lý dữ liệu
    df = pd.read_csv(FILE_DATA)
    if df.empty:
        print("Du lieu trong!")
        return

    # Chuẩn hóa về đơn vị "Per Order"
    # X: kg of CO2 per Order
    # Y: Dollars per order
    df['CO2_per_Order'] = df['Khi_Thai'] / df['So_Khach']
    df['USD_per_Order'] = df['Chi_Phi'] / df['So_Khach']

    # Nếu không có cột Kich_Ban, gán mặc định là Base Case
    if 'Kich_Ban' not in df.columns:
        df['Kich_Ban'] = 'Base Case'

    # 2. Cấu hình biểu đồ
    plt.figure(figsize=(10, 7))
    styles = {
        'Base Case':   {'color': 'royalblue',   'marker': 'o', 'label': 'Base Case'},
        'Time Window': {'color': 'crimson',     'marker': 's', 'label': 'Time Window'},
        'Density':     {'color': 'forestgreen', 'marker': '^', 'label': 'Density'}
    }

    scenarios = df['Kich_Ban'].unique()
    
    max_x = df['CO2_per_Order'].max() * 1.2 if not df.empty else 8.0
    
    for scen in scenarios:
        if scen not in styles: continue
        
        sub_df = df[df['Kich_Ban'] == scen]
        x_data = sub_df['CO2_per_Order']
        y_data = sub_df['USD_per_Order']
        
        # Vẽ các điểm phân tán
        plt.scatter(x_data, y_data, 
                    color=styles[scen]['color'], 
                    marker=styles[scen]['marker'], 
                    alpha=0.7, s=60, edgecolors='k',
                    label=f"{scen}")

        # Tính toán và vẽ đường xu hướng y = ax
        a, r2 = tinh_hoi_quy_qua_goc_0(x_data, y_data)
        
        x_trend = np.linspace(0, max_x, 100)
        y_trend = a * x_trend
        
        plt.plot(x_trend, y_trend, 
                 color=styles[scen]['color'], 
                 linestyle='--', linewidth=1.5, alpha=0.8)

        # Hiển thị phương trình và R2 lên biểu đồ
        # Vị trí text lấy theo điểm cuối của đường xu hướng
        plt.text(max_x * 0.7, a * max_x * 0.7 + random.uniform(-1, 1), 
                 f"y = {a:.4f}x\nR² = {r2:.4f}", 
                 color=styles[scen]['color'], fontsize=10, fontweight='bold')

    # 3. Định dạng trục và Trình bày
    plt.xlabel("kg of CO2 per Order", fontsize=12, fontweight='bold')
    plt.ylabel("Dollars per order", fontsize=12, fontweight='bold')
    plt.title("Wygonik & Goodchild (2010): CO2 vs Cost Trade-offs", fontsize=14, pad=15)
    
    # Bắt đầu từ gốc tọa độ (0,0)
    plt.xlim(0, max_x)
    plt.ylim(0, max_x * 4.5) # Ước lượng dải Y dựa trên slope trung bình ~3.5
    
    plt.grid(True, linestyle=':', alpha=0.6)
    plt.legend(loc='upper left', frameon=True, shadow=True)
    
    plt.tight_layout()
    
    output_img = "city_vrp_arcgis/du_lieu/bieu_do_phan_tan.png"
    plt.savefig(output_img, dpi=300)
    print(f"--- Hoan thanh! Bieu do da duoc luu tai: {output_img} ---")
    plt.show()

import random # Cần cho vị trí text ngẫu nhiên tránh đè nhau

if __name__ == "__main__":
    ve_do_thi_phan_tan_khoa_hoc()
