from PySpice.Spice.Parser import SpiceParser
import tempfile
import os

# PySpice Parser sometimes ignores content inside .subckt if it's not instantiated or if the parser strictness varies.
# Let's try to parse the file simply.

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
    circuit = parser.build_circuit()
    
    print(f"Subcircuits count: {len(circuit.subcircuits)}")
    if len(circuit.subcircuits) > 0:
        print("Found subcircuit")
    else:
        print("No subcircuit found. Dumping elements:")
        for e in circuit.elements:
            print(e)

finally:
    os.remove(tmp_path)
