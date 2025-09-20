bitmask = ['0'] * 256
inputs = ["A0", "A1", "SA", "B0", "B1", "SB", "S0", "S1"]

for idx in range(256):
    # Extract bits (order: A0=MSB, S1=LSB)
    A0 = (idx >> 7) & 1
    A1 = (idx >> 6) & 1
    SA = (idx >> 5) & 1
    B0 = (idx >> 4) & 1
    B1 = (idx >> 3) & 1
    SB = (idx >> 2) & 1
    S0 = (idx >> 1) & 1
    S1 = (idx >> 0) & 1
    
    s2 = not (S0 or S1)
    f1 = A1 if SA else A0
    f2 = B1 if SB else B0
    f_val = f2 if s2 else f1
    bitmask[idx] = '1' if f_val else '0'

lut_config = ''.join(bitmask)
print(lut_config)