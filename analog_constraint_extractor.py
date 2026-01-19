import networkx as nx
import PySpice.Logging.Logging as Logging
from PySpice.Spice.Parser import SpiceParser
import json

class AnalogConstraintExtractor:
    def __init__(self):
        self.graph = nx.MultiGraph()
        self.constraints = {"symmetry": [], "groups": []}

    def read_netlist(self, spice_file_path):
        """讀取 SPICE Netlist 並建立 PySpice 電路物件"""
        parser = SpiceParser(path=spice_file_path)
        circuit = parser.build_circuit()
        
        self._circuit_to_graph(circuit)
        
        # [Fix] PySpice build_circuit() ignores uninstantiated subcircuits.
        # But parser.subcircuits contains the list of SubCircuitStatement objects found during parsing.
        # We need to build them manually if circuit.subcircuits is empty.
        
        if hasattr(parser, 'subcircuits') and parser.subcircuits:
            # parser.subcircuits is a list of SubCircuitStatement
            # We need to turn them into SubCircuit objects to access elements easily
            for subckt_statment in parser.subcircuits:
                # Manually build the subcircuit
                # pass 0 as ground node reference (dummy)
                subckt = subckt_statment.build(0) 
                self._process_elements(subckt.elements)

    def _circuit_to_graph(self, circuit):
        """將 PySpice 電路轉換為 NetworkX 二分圖 (Bipartite Graph)"""
        self.graph.clear()
        
        # 1. 處理 Top Level Elements
        self._process_elements(circuit.elements)
        
        # 2. 處理 Circuit 物件中已知的 Subcircuits
        for subckt in circuit.subcircuits:
            self._process_elements(subckt.elements)

    def _process_elements(self, elements):
        """統一處理元件列表"""
        for element in elements:
            # 簡單判斷是否為 MOS (通常 M 開頭)
            if element.name.upper().startswith('M'):
                # 建立 Device 節點
                device_name = element.name
                # ... (後續邏輯搬移至此)
                self._add_device_node(element)

    def _add_device_node(self, element):
        """將單個元件加入圖形"""
        device_name = element.name
        # 屬性提取 (Model, W, L)
        try:
            w = str(getattr(element, 'width', ''))
            l = str(getattr(element, 'length', ''))
        except Exception:
            w = ""
            l = ""
        model = str(element.model)

        self.graph.add_node(device_name, type='device', model=model, w=w, l=l, subtype='nfet' if 'nfet' in model else 'pfet')

        try:
             pins = {
                'D': str(element.pins[0].node),
                'G': str(element.pins[1].node),
                'S': str(element.pins[2].node)
            }
        except (IndexError, AttributeError):
            return

        for pin_type, net_name in pins.items():
            if not self.graph.has_node(net_name):
                self.graph.add_node(net_name, type='net')
            self.graph.add_edge(device_name, net_name, pin=pin_type)

    def identify_diff_pairs(self):
        """識別差動對 (Differential Pairs)"""
        # 邏輯: 
        # 1. 兩顆 MOS (M1, M2)
        # 2. 相同的 Model, W, L
        # 3. Source 連接到同一個 Net (Tail)
        # 4. Drain 連接到不同的 Net (避免是並聯元件)
        
        devices = [n for n, d in self.graph.nodes(data=True) if d.get('type') == 'device']
        visited = set()

        for i in range(len(devices)):
            m1 = devices[i]
            if m1 in visited: continue
            
            for j in range(i + 1, len(devices)):
                m2 = devices[j]
                if m2 in visited: continue
                
                if self._is_diff_pair(m1, m2):
                    self.constraints["symmetry"].append({
                        "name": f"sym_{m1}_{m2}",
                        "netA": m1,  # 實際上應該是 Net 或 Block，這裡簡化為 Device
                        "netB": m2,
                        "type": "symmetry"
                    })
                    visited.add(m1)
                    visited.add(m2)
                    break

    def _is_diff_pair(self, m1, m2):
        node1 = self.graph.nodes[m1]
        node2 = self.graph.nodes[m2]

        # 檢查屬性一致性
        if node1['model'] != node2['model'] or node1['w'] != node2['w'] or node1['l'] != node2['l']:
            return False

        # 檢查連接關係
        # 取得 m1, m2 的 Source net
        s1 = self._get_neighbor_net(m1, 'S')
        s2 = self._get_neighbor_net(m2, 'S')
        
        # Source 必須共接
        if not s1 or not s2 or s1 != s2:
            return False
            
        # Drain 通常不共接 (若是共接可能是並聯)
        d1 = self._get_neighbor_net(m1, 'D')
        d2 = self._get_neighbor_net(m2, 'D')
        if d1 == d2:
            return False

        return True

    def identify_current_mirrors(self):
        """識別電流鏡 (Current Mirrors)"""
        # 邏輯:
        # 1. 兩顆 MOS (M3, M4) 共享 Gate
        # 2. 其中一顆是 Diode-connected (Gate == Drain)
        
        devices = [n for n, d in self.graph.nodes(data=True) if d.get('type') == 'device']
        # visited = set() # 避免重複加入 Constraint (如有必要)

        # 這裡簡化邏輯，只要成對就列出
        # 可能需要更複雜的 Group 邏輯處理多輸出的 Current Mirror
        
        for i in range(len(devices)):
            m1 = devices[i]
            for j in range(i + 1, len(devices)):
                m2 = devices[j]
                
                if self._is_current_mirror(m1, m2):
                    self.constraints["groups"].append({
                        "name": f"cm_{m1}_{m2}",
                        "instances": [m1, m2],
                        "type": "current_mirror"
                    })

    def _is_current_mirror(self, m1, m2):
        # 檢查 Gate 是否相連
        g1 = self._get_neighbor_net(m1, 'G')
        g2 = self._get_neighbor_net(m2, 'G')
        
        if not g1 or not g2 or g1 != g2:
            return False
            
        # 檢查是否有 Diode Connection
        # 對於 Current Mirror，Gate Net 必須等於 (M1的Drain) OR (M2的Drain)
        is_m1_diode = (g1 == self._get_neighbor_net(m1, 'D'))
        is_m2_diode = (g2 == self._get_neighbor_net(m2, 'D'))
        
        return is_m1_diode or is_m2_diode

    def _get_neighbor_net(self, device, pin_type):
        """輔助函式：取得特定 Pin 連接的 Net"""
        for neighbor in self.graph.neighbors(device):
            # 對於 MultiGraph，neighbors 仍然只回傳 distinct nodes
            # 使用 get_edge_data 獲取所有邊的資料
            # MultiGraph: get_edge_data(u, v) -> {key: {attr}, ...}
            edges = self.graph.get_edge_data(device, neighbor)
            for key, attr in edges.items():
                if attr.get('pin') == pin_type:
                    return neighbor
        return None

    def export_constraints(self, output_path):
        """輸出 Constraints 為 JSON"""
        # ALIGN 格式範例調整
        output_data = []
        
        # Symmetry constraints
        for sym in self.constraints["symmetry"]:
            output_data.append({
                "constraint": "SymmetricBlocks",
                "pairs": [[sym["netA"], sym["netB"]]],
                "direction": "V" # 假設垂直對稱
            })
            
        # Group constraints (Current Mirror)
        # ALIGN 可能沒有直接的 CurrentMirror constraint，通常也是對稱或 Group
        # 這裡示範用 Group
        for group in self.constraints["groups"]:
            output_data.append({
                "constraint": "GroupBlocks",
                "instances": group["instances"],
                "name": group["name"]
            })
            
        with open(output_path, 'w') as f:
            json.dump(output_data, f, indent=4)
        print(f"Constraints exported to {output_path}")

if __name__ == "__main__":
    # 簡單測試用
    pass
