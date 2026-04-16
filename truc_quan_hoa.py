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
    df['CO2_per_Order'] = df['Khi_Thai'] / df['So_Khach']
    df['USD_per_Order'] = df['Chi_Phi'] / df['So_Khach']

    if 'Kich_Ban' not in df.columns:
        df['Kich_Ban'] = 'Base Case'

    # 2. Khởi tạo Figure và Axes (Kích thước chuẩn 10x6)
    fig, ax = plt.subplots(figsize=(10, 6))
    
    styles = {
        'Base Case':   {'color': 'royalblue',   'marker': 'o', 'label': 'Base Case'},
        'Time Window': {'color': 'crimson',     'marker': 's', 'label': 'Time Window'},
        'Density':     {'color': 'forestgreen', 'marker': '^', 'label': 'Density'}
    }

    scenarios = df['Kich_Ban'].unique()
    
    # Tính toán giới hạn trục X để vẽ đường xu hướng
    max_x = df['CO2_per_Order'].max() * 1.1 if not df.empty else 8.0
    
    for i, scen in enumerate(scenarios):
        if scen not in styles: continue
        
        sub_df = df[df['Kich_Ban'] == scen]
        x_data = sub_df['CO2_per_Order']
        y_data = sub_df['USD_per_Order']
        
        # A. Vẽ các điểm phân tán (Scatter)
        ax.scatter(x_data, y_data, 
                    color=styles[scen]['color'], 
                    marker=styles[scen]['marker'], 
                    alpha=0.7, s=60, edgecolors='k',
                    label=f"{scen}")

        # B. Tính toán và vẽ đường hồi quy y = ax
        a, r2 = tinh_hoi_quy_qua_goc_0(x_data, y_data)
        x_trend = np.linspace(0, max_x, 100)
        y_trend = a * x_trend
        
        ax.plot(x_trend, y_trend, 
                 color=styles[scen]['color'], 
                 linestyle='--', linewidth=1.5, alpha=0.8)

        # C. Định vị Text phương trình bằng hệ tọa độ tương đối (Axes Fraction)
        # 0.95 là lề phải, y_pos giảm dần để không đè nhau
        y_pos = 0.90 - (i * 0.12)
        ax.text(0.95, y_pos, f"y = {a:.4f}x\nR² = {r2:.4f}", 
                 transform=ax.transAxes, 
                 verticalalignment='top', 
                 horizontalalignment='right',
                 color=styles[scen]['color'], 
                 fontsize=10, fontweight='bold',
                 bbox=dict(facecolor='white', alpha=0.6, edgecolor='none', boxstyle='round,pad=0.3'))

    # 3. Định dạng trục và Trình bày khoa học
    ax.set_xlabel("kg of CO2 per Order", fontsize=11, fontweight='bold')
    ax.set_ylabel("Dollars per Order", fontsize=11, fontweight='bold')
    ax.set_title("Wygonik & Goodchild (2010): Urban VRP Trade-offs", fontsize=13, pad=15)
    
    # Sử dụng Autoscale nhưng giữ gốc tọa độ (0,0)
    ax.set_xlim(left=0)
    ax.set_ylim(bottom=0)
    
    ax.grid(True, linestyle=':', alpha=0.5)
    ax.legend(loc='upper left', frameon=True, shadow=True)
    
    # Chống vỡ layout
    plt.tight_layout()
    
    output_img = "city_vrp_arcgis/du_lieu/bieu_do_phan_tan.png"
    plt.savefig(output_img, dpi=300)
    print(f"--- Hoan thanh! Bieu do đa duoc luu tai: {output_img} ---")
    plt.show()

import random # Cần cho vị trí text ngẫu nhiên tránh đè nhau

if __name__ == "__main__":
    ve_do_thi_phan_tan_khoa_hoc()
