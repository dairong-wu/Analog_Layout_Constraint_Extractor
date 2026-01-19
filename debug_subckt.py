from PySpice.Spice.Parser import SpiceParser
import tempfile
import os

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
    
    print(f"Top elements: {len(circuit.elements)}")
    print(f"Subcircuits: {len(circuit.subcircuits)}")
    if len(circuit.subcircuits) > 0:
        sub = circuit.subcircuits[0]
        print(f"Sub name: {sub.name}")
        element = sub.elements[0] # M1
        print(f"Element: {element.name}")
        try:
            print(f"Node: {element.pins[0].node}")
        except:
            print(f"Cannot access node directly")
            
        # PySpice SubCircuit pin node resolution is tricky
        # The nodes inside subckt are usually just names, but let's check.
finally:
    os.remove(tmp_path)
