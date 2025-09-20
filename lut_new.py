import itertools
import re
import sys
import math

def generate_c1_base_truth_table():
    base_int = 0
    for addr in range(256):
        # Extract inputs from address bits
        A0 = (addr >> 0) & 1
        A1 = (addr >> 1) & 1
        SA = (addr >> 2) & 1
        B0 = (addr >> 3) & 1
        B1 = (addr >> 4) & 1
        SB = (addr >> 5) & 1
        S0 = (addr >> 6) & 1
        S1 = (addr >> 7) & 1
        
        # Implement c1 logic
        f1 = A1 if SA else A0
        f2 = B1 if SB else B0
        s2 = not (S0 or S1)
        f = f2 if s2 else f1
        
        # Set the output bit
        base_int |= (f << addr)
    return base_int

def generate_c1_configurations():
    base_int = generate_c1_base_truth_table()
    permutations = list(itertools.permutations(range(8)))
    truth_tables = set()
    
    for p in permutations:
        # Create inverse permutation
        inv_p = [0] * 8
        for i in range(8):
            inv_p[p[i]] = i
        
        perm_int = 0
        for new_addr in range(256):
            # Map to original address
            old_addr = 0
            for j in range(8):
                bit = (new_addr >> inv_p[j]) & 1
                old_addr |= (bit << j)
            # Get output from base truth table
            bit_output = (base_int >> old_addr) & 1
            perm_int |= (bit_output << new_addr)
        truth_tables.add(perm_int)
    return truth_tables

def expand_k_lut(constant, k, assignment):
    """Expand k-LUT to 8-LUT using given input assignment"""
    lut8 = 0
    for addr in range(256):
        # Build index from assigned bits
        index = 0
        for i, pos in enumerate(assignment):
            bit = (addr >> pos) & 1
            index |= (bit << i)
        
        # Get output bit from constant
        if index < (1 << k):
            bit_output = (constant >> index) & 1
        else:
            bit_output = 0
        lut8 |= (bit_output << addr)
    return lut8

def parse_verilog_luts(verilog_content):
    # Improved pattern to handle Yosys output format
    pattern = r"assign\s+([\w\'\]\[_]+)\s*=\s*(\d+)'([bdh]?)([0-9a-fA-FxX_]+)\s*>>\s*(?:{([^}]+)}|([^;]+));"
    matches = re.findall(pattern, verilog_content)
    luts = []
    
    for match in matches:
        # Extract components
        width_str = match[1]
        base_char = match[2].lower()
        const_str = match[3].replace('_', '')  # Remove underscores
        signals_braced = match[4]
        signals_single = match[5]
        
        # Get width
        try:
            width = int(width_str)
        except:
            continue
            
        # Convert constant to integer
        base = 10
        if base_char == 'h': base = 16
        elif base_char == 'b': base = 2
        elif base_char == 'd': base = 10
        
        try:
            # Handle large hex constants
            if 'x' in const_str:
                const_str = const_str.split('x')[-1]
            const_int = int(const_str, base)
        except:
            continue
        
        # Mask constant to specified width
        if width > 0:
            mask = (1 << width) - 1
            const_int &= mask
        else:
            const_int = 0
            
        # Determine number of inputs (k)
        if signals_braced:
            # Count signals in braced list
            signals = [s.strip() for s in signals_braced.split(',')]
            k = len(signals)
        elif signals_single:
            # Single signal
            k = 1
        else:
            # No signals - constant LUT
            k = 0
            
        # Handle bit-slices by checking if they represent multiple bits
        actual_k = 0
        if signals_braced:
            for sig in signals:
                if ':' in sig:  # Bit slice like [1:0]
                    # Estimate bit width from slice notation
                    parts = re.findall(r'\[(\d+):(\d+)\]', sig)
                    if parts:
                        msb, lsb = map(int, parts[0])
                        actual_k += abs(msb - lsb) + 1
                    else:
                        actual_k += 1
                else:
                    actual_k += 1
        else:
            actual_k = k
            
        # For constant LUTs, k should be based on width
        if k == 0:
            k = math.ceil(math.log2(width)) if width > 0 else 0
            actual_k = k
        
        # Add to LUT list
        luts.append((actual_k, const_int))
    
    return luts

def main():
    # Step 1: Generate all c1 configurations
    print("Generating c1 configurations... (this takes ~20-30 seconds)")
    c1_configs = generate_c1_configurations()
    print(f"Generated {len(c1_configs)} unique c1 configurations")
    
    # Step 2: Read Verilog file
    if len(sys.argv) < 2:
        print("Usage: python lut_analyzer.py <verilog_file.v>")
        return
    with open(sys.argv[1]) as f:
        verilog_content = f.read()
    
    # Step 3: Extract LUTs from Verilog
    verilog_luts = parse_verilog_luts(verilog_content)
    print(f"Found {len(verilog_luts)} LUTs in Verilog")
    
    if not verilog_luts:
        print("No LUTs found. Exiting.")
        return
    
    # Step 4: Count matches with expansion
    c1_count = 0
    total_configs_generated = 0
    
    for i, (k, const_int) in enumerate(verilog_luts):
        if k == 0:
            # Constant LUT - expand to all 0s or all 1s
            bit0 = const_int & 1
            expanded_truth = (1 << 256) - 1 if bit0 else 0
            if expanded_truth in c1_configs:
                c1_count += 1
            continue
        
        print(f"Processing LUT {i+1}/{len(verilog_luts)} (k={k})...")
        
        # Generate all possible input assignments
        assignments = list(itertools.permutations(range(8), k))
        total_configs_generated += len(assignments)
        
        found = False
        for assignment in assignments:
            expanded = expand_k_lut(const_int, k, assignment)
            if expanded in c1_configs:
                found = True
                break
        
        if found:
            c1_count += 1
    
    non_c1_count = len(verilog_luts) - c1_count
    
    print("\nResults:")
    print(f"Total expanded configurations generated: {total_configs_generated}")
    print(f"LUTs matching c1 configuration: {c1_count}")
    print(f"LUTs NOT matching c1 configuration: {non_c1_count}")

if __name__ == "__main__":
    main()