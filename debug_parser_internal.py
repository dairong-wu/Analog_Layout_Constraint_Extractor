from PySpice.Spice.Parser import SpiceParser
import tempfile
import os

netlist_content = """* Debug Parser Internal
.subckt OTA in_p in_n out vdd gnd
M1 node_x in_n tail gnd sky130_fd_pr__nfet_01v8 W=10u L=0.15u
.ends
"""

with tempfile.NamedTemporaryFile(mode='w', suffix='.sp', delete=False) as tmp:
    tmp.write(netlist_content)
    tmp_path = tmp.name

try:
    parser = SpiceParser(path=tmp_path)
    # Don't build circuit, just inspect parser
    print(f"Parser Dir: {dir(parser)}")
    
    # Try simulating build_circuit process step by step
    # Or inspect _subcircuits directly after init? No, parser parses on build or implicitly
    
    # PySpice's build_circuit actually triggers the parsing.
    circuit = parser.build_circuit() 
    
    # Usually _subcircuits property exists on Parser
    if hasattr(parser, '_subcircuits'):
        print(f"Has _subcircuits: {len(parser._subcircuits)}")
        for name, sub in parser._subcircuits.items():
            print(f"Name: {name}, Elements: {len(sub.elements)}")
    else:
        print("No _subcircuits attribute found")
        
    # Check circuit subckts
    print(f"Circuit Subckts: {len(circuit.subcircuits)}")

finally:
    os.remove(tmp_path)
