import struct
import numpy as np

ROUND_SIZES = [169, 1286792, 13960050, 123156254]

with open('/home/mundhra.ve/poker_thesis/holdem_100b.abs', 'rb') as fin, \
     open('/home/mundhra.ve/poker_thesis/holdem_100b_cfrm.abs', 'wb') as fout:
    for r in range(4):
        round_num = struct.unpack('<i', fin.read(4))[0]
        nb_buckets = struct.unpack('<i', fin.read(4))[0]
        data = np.frombuffer(fin.read(4 * ROUND_SIZES[r]), dtype=np.uint32)
        
        fout.write(struct.pack('<i', round_num))
        fout.write(struct.pack('<i', ROUND_SIZES[r]))
        fout.write(data.tobytes())
        
        print(f'Round {r}: wrote {ROUND_SIZES[r]} entries with {nb_buckets} buckets')

print('Done! Output: holdem_100b_cfrm.abs')
