from PySpice.Spice.Parser import SpiceParser
import tempfile
import os

netlist_content = """* Five-Transistor OTA (Operational Transconductance Amplifier)
* This netlist contains a Differential Pair (M1, M2) and a Current Mirror (M3, M4)

.subckt OTA in_p in_n out vdd gnd
* Differential Pair
* M1/M2: Same Model, W, L. Sources connected to 'tail'.
M1 node_x in_n tail gnd sky130_fd_pr__nfet_01v8 W=10u L=0.15u
M2 out    in_p tail gnd sky130_fd_pr__nfet_01v8 W=10u L=0.15u

* Active Load (Current Mirror)
* M3/M4: Shared Gate (node_x). M3 is Diode-connected (Drain=node_x, Gate=node_x).
M3 node_x node_x vdd vdd sky130_fd_pr__pfet_01v8 W=20u L=0.5u
M4 out    node_x vdd vdd sky130_fd_pr__pfet_01v8 W=20u L=0.5u

* Tail Current Source
* (Represented as a simple Current Source here, or could be another MOS)
Iss tail gnd 200u
.ends
"""

with tempfile.NamedTemporaryFile(mode='w', suffix='.sp', delete=False) as tmp:
    tmp.write(netlist_content)
    tmp_path = tmp.name

try:
    print(f"File Size: {os.path.getsize(tmp_path)}")
    parser = SpiceParser(path=tmp_path)
    circuit = parser.build_circuit()
    
    print(f"Top Elements: {len(circuit.elements)}")
    print(f"Subcircuits: {len(circuit.subcircuits)}")
    
    if len(circuit.subcircuits) == 0:
        # Check raw parser content if possible
        # Some versions of PySpice ignore uninstantiated subckts entirely in build_circuit()
        pass

finally:
    os.remove(tmp_path)
