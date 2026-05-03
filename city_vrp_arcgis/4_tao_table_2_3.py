import os
import sys
import pandas as pd

# Xác định thư mục gốc dựa trên vị trí file này
_THU_MUC_GOC = os.path.dirname(os.path.abspath(__file__))
if _THU_MUC_GOC not in sys.path:
    sys.path.insert(0, _THU_MUC_GOC)

from giao_dien.terminal_ui import in_tieu_de

def main():
    in_tieu_de("PHASE 3: XUẤT BẢNG SO SÁNH (Wygonik & Goodchild)")
    
    csv_file = os.path.join(_THU_MUC_GOC, "ket_qua", "lich_su_so_sanh.csv")
    if not os.path.exists(csv_file):
        print("Lỗi: Không tìm thấy file lịch sử chạy. Hãy chạy File 3 trước.")
        return

    df = pd.read_csv(csv_file)
    
    # Table 2: Scenario Cost Comparisons
    print("\n--- TABLE 2: SCENARIO COST COMPARISONS ---")
    table_2 = df[["Kich_Ban", "Chi_Phi"]].copy()
    print(table_2.to_string(index=False))
    
    # Table 3: Scenario Emissions Comparisons
    print("\n--- TABLE 3: SCENARIO EMISSIONS COMPARISONS ---")
    table_3 = df[["Kich_Ban", "Khi_Thai"]].copy()
    # Tính % giảm CO2 (giả sử dòng đầu là Baseline)
    if len(df) > 1:
        baseline_kt = df.iloc[0]["Khi_Thai"]
        table_3["Giam_CO2_%"] = ((baseline_kt - table_3["Khi_Thai"]) / baseline_kt * 100).round(2)
    
    print(table_3.to_string(index=False))

if __name__ == "__main__":
    main()
