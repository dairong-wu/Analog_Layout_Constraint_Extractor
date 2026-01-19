# Analog-Layout-Constraint-Extractor 🚀

A Graph Theory-based tool for automatic extraction of analog circuit layout constraints, supporting **ALIGN** compatible formats.

This tool parses SPICE netlists, transforms them into a graph representation, and automatically identifies critical analog circuit structures (e.g., **Differential Pairs**, **Current Mirrors**). It then generates the corresponding layout constraint files required for automated placement and routing.

## ✨ Features

- **Robust SPICE Parsing**: Leverages `PySpice` to parse standard SPICE netlists.
- **Graph-Based Engine**: Utilizes `NetworkX` to construct a **Bipartite Graph** (representing Device-Net connectivity).
- **Automated Heuristic Recognition**:
    - **Differential Pairs**: Identifies pairs based on matching device models, identical sizing ($W/L$), and common-source topology.
    - **Current Mirrors**: Detects gate-sharing configurations with diode-connected reference devices.
- **ALIGN Compatibility**: Exports JSON constraint files formatted for the **ALIGN** (Analog Layout, Integrated Circuit Automatic Generation) framework.

## 🛠 Installation

Requires **Python 3.8+**.

```bash
# Install dependencies
pip install PySpice networkx matplotlib```

Note: PySpice may require a local SPICE engine installation (e.g., Ngspice).

🚀 Quick Start
1. Prepare Netlist
Prepare a .sp file (e.g., amplifier.sp).

2. Run Extraction Tool
Use the AnalogConstraintExtractor class within your script:

```Python
from src.extractor import AnalogConstraintExtractor

# Initialize with netlist content
extractor = AnalogConstraintExtractor(netlist_path="amplifier.sp")
extractor.build_graph()

# Execute recognition algorithms
extractor.identify_diff_pairs()
extractor.identify_current_mirrors()

# Export ALIGN-ready constraints
extractor.export_constraints("output/constraints.json")```
🧪 Testing
The project includes a suite of automated unit tests to verify extraction logic:

```Bash

python3 -m unittest tests/test_extractor.py```