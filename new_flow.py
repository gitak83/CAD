#!/usr/bin/env python3
import re
import os

def parse_lut_instances(verilog_content):
    """
    Parse LUT instances from the Verilog content
    Returns a list of dictionaries with lut info
    """
    lut_instances = []
    
    # Pattern to match LUT instances
    pattern = re.compile(
        r"\$lut\s*#\s*\(\s*\.LUT\(([^)]+)\)\s*,\s*\.WIDTH\(([^)]+)\)\s*\)\s*([\w$]+)\s*\(\s*\.A\(([^)]+)\)\s*,\s*\.Y\(([^)]+)\)\s*\);",
        re.MULTILINE | re.DOTALL
    )

    matches = re.findall(pattern, verilog_content)
    
    for match in matches:
        lut_value, width, instance_name, inputs, output = match
        lut_instances.append({
            'value': lut_value,
            'width': width,
            'name': instance_name,
            'inputs': inputs,
            'output': output
        })
    
    return lut_instances

def extract_lut2_config(lut_value):
    """
    Extract the 4-bit configuration from a LUT2 value string
    """
    if lut_value.startswith("4'h"):
        hex_val = lut_value[3:]
        config = int(hex_val, 16)
        # Extract the 4 bits
        b1 = (config >> 0) & 1  # Inputs (0, 0)
        b2 = (config >> 1) & 1  # Inputs (0, 1)
        b3 = (config >> 2) & 1  # Inputs (1, 0)
        b4 = (config >> 3) & 1  # Inputs (1, 1)
        return b1, b2, b3, b4
    else:
        return None

# def map_lut2_to_c1(lut_info):
#     """
#     Map a LUT2 to a c1 cell configuration
#     Returns the c1 configuration if possible
#     """
#     # Only handle LUT2
#     if not lut_info['width'] == '32\'d2':
#         return None
    
#     # Extract the configuration bits
#     config = extract_lut2_config(lut_info['value'])
#     if config is None:
#         return None
    
#     b1, b2, b3, b4 = config
    
#     # Parse the inputs
#     inputs = lut_info['inputs'].strip()
#     if inputs.startswith('{') and inputs.endswith('}'):
#         inputs = inputs[1:-1].strip()
#         input_signals = [s.strip() for s in inputs.split(',')]
#         if len(input_signals) != 2:
#             return None
#         a_signal, b_signal = input_signals
#     else:
#         # Single input (shouldn't happen for LUT2)
#         return None
    
#     # Create the c1 instance
#     c1_instance = f"c1 {lut_info['name']} ("
#     c1_instance += f".A0(1'b{b3}), .A1(1'b{b4}), .SA({b_signal}), "
#     c1_instance += f".B0(1'b{b1}), .B1(1'b{b2}), .SB({b_signal}), "
#     c1_instance += f".S0({a_signal}), .S1({a_signal}), .f({lut_info['output']}) );"
    
#     return c1_instance

def map_lut2_to_c1(lut_info):
    """
    Map a LUT to a c1 cell configuration
    Supports LUT2 (width=2) and LUT1 (width=1) cases
    """
    width = lut_info['width']

    # Handle LUT1 (WIDTH=1) separately → it's just a pass-through or constant
    if width == "32'd1":
        # Extract config (2-bit, since LUT1 has 2^1 = 2 entries)
        val = lut_info['value']
        if val.startswith("2'h"):
            hex_val = val[3:]
            config = int(hex_val, 16)
            b0 = (config >> 0) & 1  # input=0
            b1 = (config >> 1) & 1  # input=1

            # If LUT1 is identity: output = input
            if b0 == 0 and b1 == 1:
                return f"assign {lut_info['output']} = {lut_info['inputs']};"
            # If LUT1 is inversion
            elif b0 == 1 and b1 == 0:
                return f"assign {lut_info['output']} = ~{lut_info['inputs']};"
            # Constant 0
            elif b0 == 0 and b1 == 0:
                return f"assign {lut_info['output']} = 1'b0;"
            # Constant 1
            elif b0 == 1 and b1 == 1:
                return f"assign {lut_info['output']} = 1'b1;"
            else:
                return None  # shouldn't happen

    # Handle LUT2 (WIDTH=2)
    if width != "32'd2":
        return None

    config = extract_lut2_config(lut_info['value'])
    if config is None:
        return None

    b1, b2, b3, b4 = config

    inputs = lut_info['inputs'].strip()

    # Case 1: Explicit concatenation {a, b}
    if inputs.startswith('{') and inputs.endswith('}'):
        input_signals = [s.strip() for s in inputs[1:-1].split(',')]
    # Case 2: Bus slice like zero_sum[1:0]
    elif ':' in inputs:
        base, rng = inputs.split('[')
        hi, lo = map(int, rng[:-1].split(':'))
        input_signals = [f"{base}[{i}]" for i in range(lo, hi+1)]
    else:
        return None

    if len(input_signals) != 2:
        return None

    a_signal, b_signal = input_signals

    # Create the c1 instance
    c1_instance = f"c1 {lut_info['name']} ("
    c1_instance += f".A0(1'b{b3}), .A1(1'b{b4}), .SA({b_signal}), "
    c1_instance += f".B0(1'b{b1}), .B1(1'b{b2}), .SB({b_signal}), "
    c1_instance += f".S0({a_signal}), .S1({a_signal}), .f({lut_info['output']}) );"

    return c1_instance

def main():
    verilog_file = "mapped_design.v"
    
    if not os.path.exists(verilog_file):
        print(f"Error: File {verilog_file} not found")
        return
    
    # Read the Verilog file
    with open(verilog_file, 'r') as f:
        verilog_content = f.read()
    
    # Parse LUT instances
    lut_instances = parse_lut_instances(verilog_content)
    print(f"Found {len(lut_instances)} LUT instances")
    
    # Map LUT2 instances to c1 cells
    c1_instances = []
    for lut_info in lut_instances:
        c1_instance = map_lut2_to_c1(lut_info)
        if c1_instance:
            c1_instances.append(c1_instance)
            print(f"Mapped {lut_info['name']} to c1 cell")
    
    print(f"\nMapped {len(c1_instances)} out of {len(lut_instances)} LUTs to c1 cells")
    
    # Generate a new Verilog file with c1 cells
    if c1_instances:
        # Replace LUT instances with c1 instances
        new_content = verilog_content
        
        for lut_info in lut_instances:
            c1_instance = map_lut2_to_c1(lut_info)
            if c1_instance:
                # Find the original LUT instance
                lut_pattern = f"\\\\\\$lut #\\(\.LUT\\({lut_info['value']}\\),\.WIDTH\\({lut_info['width']}\\)\\) {lut_info['name']} \\(\.A\\({lut_info['inputs']}\\),\.Y\\({lut_info['output']}\\)\\);"
                new_content = re.sub(lut_pattern, c1_instance, new_content)
        
        # Add the c1 module definition at the end
        c1_module = """
module c1(input A0, A1, SA, B0, B1, SB, S0, S1, output f);
    wire f1, f2, s2;
    assign f1 = (SA) ? A1 : A0;
    assign f2 = (SB) ? B1 : B0;
    assign s2 = !(S0 | S1);
    assign f = (s2) ? f2 : f1;
endmodule
"""
        new_content += c1_module
        
        # Write the modified Verilog file
        with open("c1_mapped_design.v", 'w') as f:
            f.write(new_content)
        
        print(f"Created c1-mapped design: c1_mapped_design.v")

if __name__ == "__main__":
    main()