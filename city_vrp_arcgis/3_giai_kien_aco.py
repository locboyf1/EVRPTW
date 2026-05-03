"""
HƯỚNG DẪN TỰ CODE THUẬT TOÁN ĐÀN KIẾN (ACO)
------------------------------------------
1. Load ma trận OD:
     matrices = np.load(os.path.join(_THU_MUC_GOC, "du_lieu", "cache", "ma_tran_od.npz"))
2. Các ma trận có sẵn: matrices['cp'], matrices['kt'], matrices['tg'], matrices['km']
3. Load danh sách khách hàng:
     with open(os.path.join(_THU_MUC_GOC, "du_lieu", "khach_hang.json"), ...) as f:
4. Implement class AntColonySolver tương tự TabuSearchVRPSolver.
5. Lưu kết quả vào ket_qua/aco_ket_qua.json và append vào ket_qua/lich_su_so_sanh.csv.
"""

import os
import sys
import numpy as np
import json

# Xác định thư mục gốc dựa trên vị trí file này
_THU_MUC_GOC = os.path.dirname(os.path.abspath(__file__))
if _THU_MUC_GOC not in sys.path:
    sys.path.insert(0, _THU_MUC_GOC)

def main():
    print("Placeholder cho thuật toán Ant Colony (ACO).")
    print("Hãy làm theo hướng dẫn trong comment của file này.")

if __name__ == "__main__":
    main()
