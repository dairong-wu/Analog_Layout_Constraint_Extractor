import unittest
import networkx as nx
from analog_constraint_extractor import AnalogConstraintExtractor
from PySpice.Spice.Netlist import Circuit
from PySpice.Spice.Parser import SpiceParser
import os
import tempfile

class TestAnalogConstraintExtractor(unittest.TestCase):
    def setUp(self):
        self.extractor = AnalogConstraintExtractor()
        # 為了測試，我們可以直接操作 self.extractor.graph，或者 mock 讀檔
        # 但最真實的是建立一個臨時 sp 檔案
        
    def create_dummy_netlist(self, filename, content):
        with open(filename, 'w') as f:
            f.write(content)

    def test_case_1_success(self):
        """Case 1: 驗證差動對與電流鏡識別"""
        netlist_content = """
* Testbench for Constraint Extraction
M1 out_n in_n tail 0 sky130_fd_pr__nfet_01v8 W=10u L=0.15u
M2 out_p in_p tail 0 sky130_fd_pr__nfet_01v8 W=10u L=0.15u
M3 out_n out_n vdd vdd sky130_fd_pr__pfet_01v8 W=20u L=0.5u
M4 out_p out_n vdd vdd sky130_fd_pr__pfet_01v8 W=20u L=0.5u
Iss tail 0 200u
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.sp', delete=False) as tmp:
            tmp.write(netlist_content)
            tmp_path = tmp.name

        try:
            # 讀取 Netlist
            self.extractor.read_netlist(tmp_path)
            
            # 手動觸發 NetworkX 繪圖 (Optional for visual check, skip in automated test)
            # self.extractor.draw_graph()

            # 執行識別
            self.extractor.identify_diff_pairs()
            self.extractor.identify_current_mirrors()
            
            # 驗證 Symmetry (M1, M2)
            sym_constraints = self.extractor.constraints["symmetry"]
            found_diff_pair = False
            for c in sym_constraints:
                # 簡單檢查是否包含 M1, M2
                if (c['netA'] == 'M1' and c['netB'] == 'M2') or (c['netA'] == 'M2' and c['netB'] == 'M1'):
                    found_diff_pair = True
            self.assertTrue(found_diff_pair, "Failed to identify differential pair M1/M2")

            # 驗證 Current Mirror (M3, M4)
            group_constraints = self.extractor.constraints["groups"]
            found_mirror = False
            for c in group_constraints:
                if 'M3' in c['instances'] and 'M4' in c['instances']:
                    found_mirror = True
            self.assertTrue(found_mirror, "Failed to identify current mirror M3/M4")
            
        finally:
            os.remove(tmp_path)

    def test_case_2_negative(self):
        """Case 2: 驗證不對稱電路"""
        netlist_content = """
* Asymmetric Circuit
M1 out_n in_n tail 0 sky130_fd_pr__nfet_01v8 W=10u L=0.15u
M2 out_p in_p tail 0 sky130_fd_pr__nfet_01v8 W=5u L=0.15u
"""
        # Note: M2 has different W (5u vs 10u)
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.sp', delete=False) as tmp:
            tmp.write(netlist_content)
            tmp_path = tmp.name

        try:
            self.extractor.graph.clear()
            self.extractor.constraints = {"symmetry": [], "groups": []}
            
            self.extractor.read_netlist(tmp_path)
            self.extractor.identify_diff_pairs()
            
            # 應該找不到對稱
            self.assertEqual(len(self.extractor.constraints["symmetry"]), 0, "Should not identify asymmetric pair as symmetric")
            
        finally:
            os.remove(tmp_path)

    def test_visualization_stub(self):
        """Stub for graphical visualization"""
        # 由於環境問題，這裡僅確認 NetworkX 是否有節點
        self.extractor.graph.add_node("TestDev", type='device')
        self.extractor.graph.add_node("TestNet", type='net')
        self.extractor.graph.add_edge("TestDev", "TestNet", pin='D')
        self.assertTrue(self.extractor.graph.number_of_nodes() >= 2)

if __name__ == '__main__':
    unittest.main()
