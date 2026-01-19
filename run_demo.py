from analog_constraint_extractor import AnalogConstraintExtractor
import json
import os

def run_demo():
    print("--- Running Demo with amplifier.sp ---")
    
    # 1. Initialize Extractor
    extractor = AnalogConstraintExtractor()
    
    # 2. Read Netlist
    spice_file = "amplifier.sp"
    if not os.path.exists(spice_file):
        print(f"Error: {spice_file} not found.")
        return

    print(f"Reading {spice_file}...")
    extractor.read_netlist(spice_file)
    
    # 3. Identify Structures
    print("Identifying Differential Pairs...")
    extractor.identify_diff_pairs()
    
    print("Identifying Current Mirrors...")
    extractor.identify_current_mirrors()
    
    # 4. Export Results
    output_file = "amplifier_constraints.json"
    extractor.export_constraints(output_file)
    print(f"Constraints exported to {output_file}")
    
    # 5. Show Content
    print("\n--- Generated Constraints Content ---")
    with open(output_file, 'r') as f:
        print(json.dumps(json.load(f), indent=4))

if __name__ == "__main__":
    run_demo()
