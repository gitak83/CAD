import itertools
import re
import sys
import math

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
        
        if s1 and s0:
            out = D11
        elif s1 and not s0:
            out = D10
        elif not s1 and s0:
            out = D01
        else:  # not s1 and not s0
            out = D00
            
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

def expand_k_lut(constant, k, assignment):
    lut8 = 0
    for addr in range(256):
        index = 0
        for i, pos in enumerate(assignment):
            bit = (addr >> pos) & 1
            index |= (bit << i)
        if index < (1 << k):
            bit_output = (constant >> index) & 1
        else:
            bit_output = 0
        lut8 |= (bit_output << addr)
    return lut8

def parse_verilog_luts(verilog_content):
    pattern = r"assign\s+([\w\'\]\[_]+)\s*=\s*(\d+)'([bdh]?)([0-9a-fA-FxX_]+)\s*>>\s*(?:{([^}]+)}|([^;]+));"
    matches = re.findall(pattern, verilog_content)
    luts = []
    
    for match in matches:
        width_str = match[1]
        base_char = match[2].lower()
        const_str = match[3].replace('_', '')
        signals_braced = match[4]
        signals_single = match[5]
        
        try:
            width = int(width_str)
        except:
            continue
            
        base = 10
        if base_char == 'h': base = 16
        elif base_char == 'b': base = 2
        elif base_char == 'd': base = 10
        
        try:
            if 'x' in const_str:
                const_str = const_str.split('x')[-1]
            const_int = int(const_str, base)
        except:
            continue
        
        if width > 0:
            mask = (1 << width) - 1
            const_int &= mask
        else:
            const_int = 0
            
        if signals_braced:
            signals = [s.strip() for s in signals_braced.split(',')]
            k = 0
            for sig in signals:
                if ':' in sig:
                    parts = re.findall(r'\[(\d+):(\d+)\]', sig)
                    if parts:
                        msb, lsb = map(int, parts[0])
                        k += abs(msb - lsb) + 1
                    else:
                        k += 1
                else:
                    k += 1
        elif signals_single:
            k = 1
        else:
            k = 0
            
        if k == 0:
            k = math.ceil(math.log2(width)) if width > 0 else 0
        
        luts.append((k, const_int))
    
    return luts

def main():
    # Generate configurations for both modules
    print("Generating c1 configurations...")
    c1_configs = generate_module_configurations(generate_c1_base_truth_table)
    print(f"Generated {len(c1_configs)} unique c1 configurations")
    
    print("Generating c2 configurations...")
    c2_configs = generate_module_configurations(generate_c2_base_truth_table)
    print(f"Generated {len(c2_configs)} unique c2 configurations")
    
    # Read Verilog file
    if len(sys.argv) < 2:
        print("Usage: python lut_analyzer.py <verilog_file.v>")
        return
    with open(sys.argv[1]) as f:
        verilog_content = f.read()
    
    # Extract LUTs
    verilog_luts = parse_verilog_luts(verilog_content)
    print(f"Found {len(verilog_luts)} LUTs in Verilog")
    
    if not verilog_luts:
        print("No LUTs found. Exiting.")
        return
    
    # Process LUTs
    c1_count = 0
    c2_count = 0
    both_count = 0
    total_configs_generated = 0
    
    for i, (k, const_int) in enumerate(verilog_luts):
        print(f"Processing LUT {i+1}/{len(verilog_luts)} (k={k})...")
        
        if k == 0:
            # Handle constant LUT
            bit0 = const_int & 1
            expanded = (1 << 256) - 1 if bit0 else 0
            c1_match = expanded in c1_configs
            c2_match = expanded in c2_configs
            if c1_match and c2_match:
                both_count += 1
                c1_count += 1
                c2_count += 1
            elif c1_match:
                c1_count += 1
            elif c2_match:
                c2_count += 1
            continue
        
        # Generate all possible input assignments
        assignments = list(itertools.permutations(range(8), k))
        total_configs_generated += len(assignments)
        
        found_c1 = False
        found_c2 = False
        
        for assignment in assignments:
            expanded = expand_k_lut(const_int, k, assignment)
            
            if not found_c1 and expanded in c1_configs:
                found_c1 = True
            if not found_c2 and expanded in c2_configs:
                found_c2 = True
            if found_c1 and found_c2:
                break
        
        if found_c1 and found_c2:
            both_count += 1
            c1_count += 1
            c2_count += 1
        elif found_c1:
            c1_count += 1
        elif found_c2:
            c2_count += 1
    
    non_count = len(verilog_luts) - (c1_count + c2_count - both_count)
    
    print("\nResults:")
    print(f"Total expanded configurations generated: {total_configs_generated}")
    print(f"LUTs matching c1 configuration: {c1_count} ({both_count} also match c2)")
    print(f"LUTs matching c2 configuration: {c2_count}")
    print(f"LUTs matching both configurations: {both_count}")
    print(f"LUTs NOT matching any configuration: {non_count}")

if __name__ == "__main__":
    main()