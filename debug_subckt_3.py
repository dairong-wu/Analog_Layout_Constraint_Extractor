from PySpice.Spice.Parser import SpiceParser
import tempfile
import os

# 試試看使用 include 或直接定義
netlist_content = """* Debug Subckt
.subckt OTA in_p in_n out vdd gnd
M1 node_x in_n tail gnd sky130_fd_pr__nfet_01v8 W=10u L=0.15u
.ends
"""

with tempfile.NamedTemporaryFile(mode='w', suffix='.sp', delete=False) as tmp:
    tmp.write(netlist_content)
    tmp_path = tmp.name

try:
    parser = SpiceParser(path=tmp_path)
    # PySpice 可能只建立 TopCircuit，需要檢查是否正確解析了 subckt 定義
    circuit = parser.build_circuit()
    
    # 檢查 parser._subcircuits (私有屬性，僅作 Debug)
    # PySpice 的 parser.build_circuit() 會回傳一個 Circuit 物件
    # 按照文件，subcircuits 應該是 circuit 的屬性
    
    print(f"Circuit Name: {circuit.title}")
    print(f"Subcircuits: {circuit.subcircuits}")

finally:
    os.remove(tmp_path)
