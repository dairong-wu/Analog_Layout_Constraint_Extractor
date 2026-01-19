from PySpice.Spice.Parser import SpiceParser
import tempfile
import os

netlist_content = """* Instantiated Subckt
.subckt OTA in_p in_n out vdd gnd
M1 node_x in_n tail gnd sky130_fd_pr__nfet_01v8 W=10u L=0.15u
M2 out    in_p tail gnd sky130_fd_pr__nfet_01v8 W=10u L=0.15u
.ends

X1 in_p in_n out vdd gnd OTA
"""

with tempfile.NamedTemporaryFile(mode='w', suffix='.sp', delete=False) as tmp:
    tmp.write(netlist_content)
    tmp_path = tmp.name

try:
    parser = SpiceParser(path=tmp_path)
    circuit = parser.build_circuit()
    
    print(f"Subcircuits: {len(circuit.subcircuits)}")
    for sub in circuit.subcircuits:
        print(f"Sub: {sub.name}")
        for e in sub.elements:
            print(f"  {e.name}")
finally:
    os.remove(tmp_path)
