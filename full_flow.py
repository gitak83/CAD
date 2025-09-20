#!/usr/bin/env python3
import itertools
import os
import subprocess
import sys
import re
import math

# ----------------------------
# Configuration Functions
# ----------------------------

def generate_c1_base_truth_table():
    base_int = 0
    for addr in range(256):
        A0 = (addr >> 0) & 1
        A1 = (addr >> 1) & 1
        SA = (addr >> 2) & 1
        B0 = (addr >> 3) & 1
        B1 = (addr >> 4) & 1
        SB = (addr >> 5) & 1
        S0 = (addr >> 6) & 1
        S1 = (addr >> 7) & 1
        
        f1 = A1 if SA else A0
        f2 = B1 if SB else B0
        s2 = not (S0 or S1)
        f = f2 if s2 else f1
        base_int |= (f << addr)
    return base_int

def generate_c2_base_truth_table():
    base_int = 0
    for addr in range(256):
        D00 = (addr >> 0) & 1
        D01 = (addr >> 1) & 1
        D10 = (addr >> 2) & 1
        D11 = (addr >> 3) & 1
        A1 = (addr >> 4) & 1
        B1 = (addr >> 5) & 1
        A0 = (addr >> 6) & 1
        B0 = (addr >> 7) & 1
        
        s1 = not (A1 or B1)
        s0 = not (A0 and B0)
        
        if s1 and s0: out = D11
        elif s1 and not s0: out = D10
        elif not s1 and s0: out = D01
        else: out = D00
            
        base_int |= (out << addr)
    return base_int

def generate_module_configurations(module_func):
    base_int = module_func()
    permutations = list(itertools.permutations(range(8)))
    truth_tables = set()
    
    for p in permutations:
        inv_p = [0] * 8
        for i in range(8):
            inv_p[p[i]] = i
        
        perm_int = 0
        for new_addr in range(256):
            old_addr = 0
            for j in range(8):
                bit = (new_addr >> inv_p[j]) & 1
                old_addr |= (bit << j)
            bit_output = (base_int >> old_addr) & 1
            perm_int |= (bit_output << new_addr)
        truth_tables.add(perm_int)
    return truth_tables

# ----------------------------
# File Generation Functions
# ----------------------------

def generate_liberty_file(c1_configs, c2_configs, filename):
    print(f"Creating Liberty file: {filename}")
    with open(filename, 'w') as f:
        # Write library header
        f.write('library(custom_luts) {\n')
        f.write('  operating_conditions(typical) {\n')
        f.write('    process : 1.0;\n')
        f.write('    voltage : 1.0;\n')
        f.write('    temperature : 25;\n')
        f.write('  }\n\n')
        
        f.write('  delay_model : table_lookup;\n')
        f.write('  lu_table_template(delay_template) {\n')
        f.write('    variable_1 : input_net_transition;\n')
        f.write('    variable_2 : total_output_net_capacitance;\n')
        f.write('    index_1("0.1, 0.5, 1.0");\n')
        f.write('    index_2("0.1, 1.0, 2.0");\n')
        f.write('  }\n\n')
        
        # Write c1 LUT definitions
        for i, config in enumerate(c1_configs):
            hex_config = f"{config:064x}"
            f.write(f'  cell(lut_c1_{i}) {{\n')
            f.write('    area : 1.0;\n')
            f.write(f'    lut : "0x{hex_config}";\n')
            f.write('    pin(A) {\n')
            f.write('      direction : input;\n')
            f.write('      capacitance : 0.001;\n')
            f.write('      timing() {\n')
            f.write('        timing_type : combinational;\n')
            f.write('        related_pin : "A";\n')
            f.write('        cell_rise(delay_template) {\n')
            f.write('          values("0.15, 0.25, 0.35", "0.2, 0.3, 0.4", "0.25, 0.35, 0.45");\n')
            f.write('        }\n')
            f.write('        cell_fall(delay_template) {\n')
            f.write('          values("0.15, 0.25, 0.35", "0.2, 0.3, 0.4", "0.25, 0.35, 0.45");\n')
            f.write('        }\n')
            f.write('      }\n')
            f.write('    }\n')
            f.write('    pin(Y) {\n')
            f.write('      direction : output;\n')
            f.write('      timing() {\n')
            f.write('        timing_type : combinational;\n')
            f.write('        related_pin : "A";\n')
            f.write('        cell_rise(delay_template) {\n')
            f.write('          values("0.15, 0.25, 0.35", "0.2, 0.3, 0.4", "0.25, 0.35, 0.45");\n')
            f.write('        }\n')
            f.write('        cell_fall(delay_template) {\n')
            f.write('          values("0.15, 0.25, 0.35", "0.2, 0.3, 0.4", "0.25, 0.35, 0.45");\n')
            f.write('        }\n')
            f.write('      }\n')
            f.write('    }\n')
            f.write('  }\n\n')
        
        # Write c2 LUT definitions
        for i, config in enumerate(c2_configs):
            hex_config = f"{config:064x}"
            f.write(f'  cell(lut_c2_{i}) {{\n')
            f.write('    area : 1.0;\n')
            f.write(f'    lut : "0x{hex_config}";\n')
            f.write('    pin(A) {\n')
            f.write('      direction : input;\n')
            f.write('      capacitance : 0.001;\n')
            f.write('      timing() {\n')
            f.write('        timing_type : combinational;\n')
            f.write('        related_pin : "A";\n')
            f.write('        cell_rise(delay_template) {\n')
            f.write('          values("0.15, 0.25, 0.35", "0.2, 0.3, 0.4", "0.25, 0.35, 0.45");\n')
            f.write('        }\n')
            f.write('        cell_fall(delay_template) {\n')
            f.write('          values("0.15, 0.25, 0.35", "0.2, 0.3, 0.4", "0.25, 0.35, 0.45");\n')
            f.write('        }\n')
            f.write('      }\n')
            f.write('    }\n')
            f.write('    pin(Y) {\n')
            f.write('      direction : output;\n')
            f.write('      timing() {\n')
            f.write('        timing_type : combinational;\n')
            f.write('        related_pin : "A";\n')
            f.write('        cell_rise(delay_template) {\n')
            f.write('          values("0.15, 0.25, 0.35", "0.2, 0.3, 0.4", "0.25, 0.35, 0.45");\n')
            f.write('        }\n')
            f.write('        cell_fall(delay_template) {\n')
            f.write('          values("0.15, 0.25, 0.35", "0.2, 0.3, 0.4", "0.25, 0.35, 0.45");\n')
            f.write('        }\n')
            f.write('      }\n')
            f.write('    }\n')
            f.write('  }\n\n')
        
        # Add flip-flop cells
        f.write('''
  // D Flip-Flop with Enable and Reset
  cell(DFFRE) {
    area: 1.5;
    ff(IQ) {
      next_state: "D";
      clocked_on: "CLK";
      clear: "R" !RESET_MODE;
      preset: "SET" !SET_MODE;
    }
    pin(CLK) {
      direction: input;
      clock: true;
      capacitance: 0.001;
      timing() {
        timing_type: rising_edge;
        intrinsic_rise: 0.1;
        intrinsic_fall: 0.1;
      }
    }
    pin(D) {
      direction: input;
      capacitance: 0.001;
      timing() {
        timing_type: setup_rising;
        related_pin: "CLK";
        intrinsic_rise: 0.05;
        intrinsic_fall: 0.05;
      }
    }
    pin(E) {
      direction: input;
      capacitance: 0.001;
      timing() {
        timing_type: setup_rising;
        related_pin: "CLK";
        intrinsic_rise: 0.05;
        intrinsic_fall: 0.05;
      }
    }
    pin(R) {
      direction: input;
      capacitance: 0.001;
      timing() {
        timing_type: setup_rising;
        related_pin: "CLK";
        intrinsic_rise: 0.05;
        intrinsic_fall: 0.05;
      }
    }
    pin(Q) {
      direction: output;
      function: "IQ";
      timing() {
        timing_type: rising_edge;
        related_pin: "CLK";
        intrinsic_rise: 0.1;
        intrinsic_fall: 0.1;
      }
    }
  }
  
  // Simple D Flip-Flop
  cell(DFF) {
    area: 1.0;
    ff(IQ) {
      next_state: "D";
      clocked_on: "CLK";
    }
    pin(CLK) {
      direction: input;
      clock: true;
      capacitance: 0.001;
      timing() {
        timing_type: rising_edge;
        intrinsic_rise: 0.1;
        intrinsic_fall: 0.1;
      }
    }
    pin(D) {
      direction: input;
      capacitance: 0.001;
      timing() {
        timing_type: setup_rising;
        related_pin: "CLK";
        intrinsic_rise: 0.05;
        intrinsic_fall: 0.05;
      }
    }
    pin(Q) {
      direction: output;
      function: "IQ";
      timing() {
        timing_type: rising_edge;
        related_pin: "CLK";
        intrinsic_rise: 0.1;
        intrinsic_fall: 0.1;
      }
    }
  }
''')
        f.write('}\n')
    print(f"Liberty file created: {filename} ({len(c1_configs) + len(c2_configs)} LUT cells + flip-flops)")

def generate_yosys_script(liberty_file, verilog_file, top_module, output_file):
    script_content = f"""# Custom Synthesis Script for c1/c2 LUTs
# Load design
read_verilog {verilog_file}

# Generic synthesis
synth -top {top_module} -lut 8

# Technology mapping with custom library
abc -liberty {liberty_file} -dress

# Clean up
clean -purge

# Write output
write_verilog -noexpr {output_file}
"""
    script_path = "custom_synth.ys"
    with open(script_path, "w") as f:
        f.write(script_content)
    print(f"Yosys script created: {script_path}")
    return script_path

# ----------------------------
# Verification Functions
# ----------------------------

def verify_mapping(verilog_file):
    try:
        with open(verilog_file) as f:
            content = f.read()
        
        # Count custom LUTs
        c1_count = len(re.findall(r"lut_c1_\d+", content))
        c2_count = len(re.findall(r"lut_c2_\d+", content))
        lut_count = c1_count + c2_count
        
        # Count flip-flops
        ff_count = len(re.findall(r"\\DFF", content)) + len(re.findall(r"\\DFFRE", content))
        
        print(f"\nVerification Results:")
        print(f"  Total custom LUTs: {lut_count}")
        print(f"    c1 LUTs: {c1_count}")
        print(f"    c2 LUTs: {c2_count}")
        print(f"  Flip-flops: {ff_count}")
        
        # Verify no generic LUTs remain
        generic_count = len(re.findall(r"\\\$lut", content))
        if generic_count > 0:
            print(f"  Warning: {generic_count} generic LUTs found!")
        else:
            print("  All combinational logic uses custom LUTs")
        
        return lut_count > 0
    except FileNotFoundError:
        print(f"Error: Output file {verilog_file} not found")
        return False

# ----------------------------
# Main Workflow
# ----------------------------

def main():
    # Configuration
    verilog_file = "counter5.v"
    top_module = "Counter_5bit"
    output_file = "mapped_design.v"
    liberty_dir = "custom_liberty"
    liberty_file = os.path.join(liberty_dir, "custom_luts.lib")
    
    print("="*60)
    print("Starting Custom LUT Synthesis Flow")
    print("="*60)
    
    # Step 1: Create output directory
    os.makedirs(liberty_dir, exist_ok=True)
    
    # Step 2: Generate LUT configurations
    print("\n" + "="*20)
    print("Generating LUT Configurations")
    print("="*20)
    print("Generating c1 configurations...")
    c1_configs = generate_module_configurations(generate_c1_base_truth_table)
    print(f"  Generated {len(c1_configs)} unique c1 configurations")
    
    print("Generating c2 configurations...")
    c2_configs = generate_module_configurations(generate_c2_base_truth_table)
    print(f"  Generated {len(c2_configs)} unique c2 configurations")
    
    # Step 3: Generate Liberty file (with flip-flops)
    print("\n" + "="*20)
    print("Generating Liberty File")
    print("="*20)
    generate_liberty_file(c1_configs, c2_configs, liberty_file)
    
    # Step 4: Generate Yosys script
    print("\n" + "="*20)
    print("Generating Synthesis Script")
    print("="*20)
    script_path = generate_yosys_script(liberty_file, verilog_file, top_module, output_file)
    
    # Step 5: Run Yosys synthesis
    print("\n" + "="*20)
    print("Running Synthesis with Yosys")
    print("="*20)
    print("This may take several minutes...")
    try:
        result = subprocess.run(["yosys", "-s", script_path], 
                                capture_output=True, text=True, check=True)
        print("Yosys synthesis completed successfully!")
        
        # Print warnings and errors
        if "Warning" in result.stdout:
            print("\nYosys warnings:")
            print("\n".join(line for line in result.stdout.splitlines() if "Warning" in line))
        if "ERROR" in result.stdout:
            print("\nYosys errors:")
            print("\n".join(line for line in result.stdout.splitlines() if "ERROR" in line))
    except subprocess.CalledProcessError as e:
        print(f"Yosys synthesis failed with error {e.returncode}:")
        print(e.stderr)
        sys.exit(1)
    except FileNotFoundError:
        print("Error: Yosys not found. Please ensure Yosys is installed and in your PATH.")
        sys.exit(1)
    
    # Step 6: Verify results
    print("\n" + "="*20)
    print("Verifying Results")
    print("="*20)
    if not os.path.exists(output_file):
        print(f"Error: Output file {output_file} not created")
        sys.exit(1)
    
    success = verify_mapping(output_file)
    
    print("\n" + "="*60)
    if success:
        print("SUCCESS: Custom LUT synthesis completed!")
        print(f"Output design: {output_file}")
    else:
        print("WARNING: Verification failed - check output for issues")
    print("="*60)

if __name__ == "__main__":
    main()