import networkx as nx
from PySpice.Spice.Parser import SpiceParser
import json

class AnalogConstraintExtractor:
    def __init__(self):
        self.graph = nx.MultiGraph()
        self.constraints = {"symmetry": [], "groups": []}

    def read_netlist(self, spice_file_path):
        """Read SPICE Netlist and build PySpice circuit object"""
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
        """Convert PySpice circuit to NetworkX Bipartite Graph"""
        self.graph.clear()
        
        # 1. Process Top Level Elements
        self._process_elements(circuit.elements)
        
        # 2. Process Known Subcircuits in Circuit object
        for subckt in circuit.subcircuits:
            self._process_elements(subckt.elements)

    def _process_elements(self, elements):
        """Unified processing for element lists"""
        for element in elements:
            # Simple check for MOS (Usually starts with M)
            if element.name.upper().startswith('M'):
                self._add_device_node(element)

    def _add_device_node(self, element):
        """Add a single device to the graph"""
        device_name = element.name
        # Attribute Extraction (Model, W, L)
        # PySpice parsed parameters usually map directly to attributes
        # W -> width, L -> length
        try:
            w = str(getattr(element, 'width', ''))
            l = str(getattr(element, 'length', ''))
        except Exception:
            # Fallback if attributes are missing
            w = ""
            l = ""

        model = str(element.model)

        self.graph.add_node(device_name, type='device', model=model, w=w, l=l, subtype='nfet' if 'nfet' in model else 'pfet')

        # Connect Nets
        # element.pins is a list, usually ordered Drain, Gate, Source, Bulk
        # Use str(pin.node) to get the connected Net name
        try:
             pins = {
                'D': str(element.pins[0].node),
                'G': str(element.pins[1].node),
                'S': str(element.pins[2].node)
            }
        except (IndexError, AttributeError):
            # Skip or log if pin count is incorrect or parsing fails
            return

        for pin_type, net_name in pins.items():
            # Ensure Net node exists
            if not self.graph.has_node(net_name):
                self.graph.add_node(net_name, type='net')
            
            # Create Edge (Device -> Net), mark pin type
            # MultiGraph allows duplicate edges, necessary for Diode-connected (D and G to same Net)
            self.graph.add_edge(device_name, net_name, pin=pin_type)

    def identify_diff_pairs(self):
        """Identify Differential Pairs"""
        # Logic: 
        # 1. Two MOS devices (M1, M2)
        # 2. Same Model, W, L
        # 3. Sources connected to the same Net (Tail)
        # 4. Drains connected to different Nets (avoid parallel devices)
        
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
                        "netA": m1,  # Should technically be Net or Block, simplified to Device here
                        "netB": m2,
                        "type": "symmetry"
                    })
                    visited.add(m1)
                    visited.add(m2)
                    break

    def _is_diff_pair(self, m1, m2):
        node1 = self.graph.nodes[m1]
        node2 = self.graph.nodes[m2]

        # Check attribute consistency
        if node1['model'] != node2['model'] or node1['w'] != node2['w'] or node1['l'] != node2['l']:
            return False

        # Check connectivity
        # Get Source net for m1, m2
        s1 = self._get_neighbor_net(m1, 'S')
        s2 = self._get_neighbor_net(m2, 'S')
        
        # Sources must be shared
        if not s1 or not s2 or s1 != s2:
            return False
            
        # Drains usually not shared (if shared, might be parallel devices)
        d1 = self._get_neighbor_net(m1, 'D')
        d2 = self._get_neighbor_net(m2, 'D')
        if d1 == d2:
            return False

        return True

    def identify_current_mirrors(self):
        """Identify Current Mirrors"""
        # Logic:
        # 1. Two MOS devices (M3, M4) share Gate
        # 2. One of them is Diode-connected (Gate == Drain)
        
        devices = [n for n, d in self.graph.nodes(data=True) if d.get('type') == 'device']
        # visited = set() # Avoid adding duplicate Constraint if necessary

        # Simplified logic: list all pairs found
        # May need more complex Group logic for multi-output Current Mirrors
        
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
        # Check if Gates are connected
        g1 = self._get_neighbor_net(m1, 'G')
        g2 = self._get_neighbor_net(m2, 'G')
        
        if not g1 or not g2 or g1 != g2:
            return False
            
        # Check for Diode Connection
        # For Current Mirror, Gate Net must equal (M1 Drain) OR (M2 Drain)
        is_m1_diode = (g1 == self._get_neighbor_net(m1, 'D'))
        is_m2_diode = (g2 == self._get_neighbor_net(m2, 'D'))
        
        return is_m1_diode or is_m2_diode

    def _get_neighbor_net(self, device, pin_type):
        """Helper: Get Net connected to a specific Pin"""
        for neighbor in self.graph.neighbors(device):
            # For MultiGraph, neighbors returns distinct nodes
            # Use get_edge_data to get all edges
            # MultiGraph: get_edge_data(u, v) -> {key: {attr}, ...}
            edges = self.graph.get_edge_data(device, neighbor)
            for key, attr in edges.items():
                if attr.get('pin') == pin_type:
                    return neighbor
        return None

    def export_constraints(self, output_path):
        """Export Constraints to JSON"""
        # ALIGN format adjustments
        output_data = []
        
        # Symmetry constraints
        for sym in self.constraints["symmetry"]:
            output_data.append({
                "constraint": "SymmetricBlocks",
                "pairs": [[sym["netA"], sym["netB"]]],
                "direction": "V" # Assume Vertical Symmetry
            })
            
        # Group constraints (Current Mirror)
        # ALIGN might not have direct CurrentMirror constraint, typically Symmetry or Group
        # Using Group here as example
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
    # Simple test stub
    pass
