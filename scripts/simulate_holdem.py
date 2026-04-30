#!/usr/bin/env python3
"""
Nash EV simulation for hold'em.
Deals random hands, both players follow Nash strategies, measures P0 chip EV.
"""
import sys, subprocess, re, ctypes, random, argparse

PRINT_STRATEGY = "/home/mundhra.ve/poker_thesis/open-pure-cfr-buckets/print_player_strategy"
HANDRANKS      = "/home/mundhra.ve/poker_thesis/poker-cfrm/handranks.dat"
ABS_FILE       = "/home/mundhra.ve/poker_thesis/holdem_100b_cfrm.abs"
ENGINE_SO      = "/home/mundhra.ve/poker_thesis/holdem_engine.so"

# Game parameters (holdem.limit.2p.36_36.game)
# blind = 2 1: P0=SB=2, P1=BB=1
# firstPlayer = 2 1 1 1: preflop P1 (1-indexed=2) acts first = player index 1
BLINDS        = [2, 1]
RAISE_SIZE    = [2, 2, 4, 4]
MAX_RAISES    = [2, 3, 3, 3]
FIRST_PLAYER  = [1, 0, 0, 0]
NUM_ROUNDS    = 4
STACK         = 36
BB_SIZE       = 2.0
NUM_BOARD     = [0, 3, 1, 1]  # board cards dealt each round

def load_engine():
    lib = ctypes.CDLL(ENGINE_SO)
    lib.engine_init.restype = ctypes.c_int
    lib.engine_init.argtypes = [ctypes.c_char_p, ctypes.c_char_p]
    lib.get_bucket.restype = ctypes.c_int
    lib.get_bucket.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_int,
                                ctypes.POINTER(ctypes.c_uint8), ctypes.c_int]
    lib.deal_hand.restype = None
    lib.deal_hand.argtypes = [ctypes.POINTER(ctypes.c_uint8),
                               ctypes.POINTER(ctypes.c_uint8),
                               ctypes.POINTER(ctypes.c_uint8)]
    lib.eval_showdown.restype = ctypes.c_int
    lib.eval_showdown.argtypes = [ctypes.POINTER(ctypes.c_uint8),
                                   ctypes.POINTER(ctypes.c_uint8),
                                   ctypes.POINTER(ctypes.c_uint8)]
    ret = lib.engine_init(HANDRANKS.encode(), ABS_FILE.encode())
    if ret != 0:
        print("engine_init failed"); sys.exit(1)
    return lib

def parse_strategy(player_file):
    result = subprocess.run([PRINT_STRATEGY, player_file, "--max-round=4"],
                            capture_output=True, text=True)
    strategy = {}
    cur_player, cur_state = None, None
    for line in result.stdout.splitlines():
        m = re.match(r'=== PLAYER (\d+) ===', line)
        if m: cur_player = int(m.group(1)) - 1; continue
        m = re.match(r'STATE:(\S+)', line)
        if m: cur_state = m.group(1); continue
        m = re.match(r'\s+Bucket (\d+): (.+)', line)
        if m and cur_player is not None and cur_state is not None:
            bucket = int(m.group(1))
            actions = {}
            for part in m.group(2).split():
                pm = re.match(r'([\d.e+\-]+)%([fcr])', part)
                if pm:
                    actions[pm.group(2)] = float(pm.group(1)) / 100.0
            strategy[(cur_player, cur_state, bucket)] = actions
    return strategy

def sample_action(strategy, player, state, bucket, legal):
    d = strategy.get((player, state, bucket), {})
    total = sum(d.get(a, 0.0) for a in legal)
    probs = [d.get(a,0.0)/total if total>1e-10 else 1.0/len(legal) for a in legal]
    r = random.random()
    cum = 0.0
    for a, p in zip(legal, probs):
        cum += p
        if r <= cum: return a
    return legal[-1]

def get_legal(p0c, p1c, p0s, p1s, raises, round_num):
    la = []
    if p0c != p1c: la.append('f')
    la.append('c')
    if raises < MAX_RAISES[round_num]:
        deficit = abs(p0c - p1c)
        rs = RAISE_SIZE[round_num]
        # check current player has enough — we check both since we don't
        # pass cur_player here; caller must verify
        la.append('r')
    return la

def simulate_hand(strategy, lib):
    """Simulate one hold'em hand. Returns P0 chip gain."""
    # Deal
    h0 = (ctypes.c_uint8*2)()
    h1 = (ctypes.c_uint8*2)()
    board = (ctypes.c_uint8*5)()
    lib.deal_hand(h0, h1, board)

    # Track board cards dealt so far
    board_so_far = (ctypes.c_uint8*5)()
    num_board_so_far = 0

    # Blinds
    p0c, p1c = BLINDS[0], BLINDS[1]
    p0s = STACK - p0c
    p1s = STACK - p1c

    state = '0:'
    round_num = 0
    cur_player = FIRST_PLAYER[0]
    raises = 0
    acted = 0
    last_was_raise = False

    while True:
        # Get bucket for current player at current round
        bkt = lib.get_bucket(round_num,
                              int(h0[0]), int(h0[1]),
                              board_so_far, num_board_so_far) if cur_player==0 else \
              lib.get_bucket(round_num,
                              int(h1[0]), int(h1[1]),
                              board_so_far, num_board_so_far)

        # Legal actions
        la = []
        if p0c != p1c: la.append('f')
        la.append('c')
        if raises < MAX_RAISES[round_num]:
            deficit = abs(p0c - p1c)
            rs = RAISE_SIZE[round_num]
            stack = p0s if cur_player==0 else p1s
            if stack >= deficit + rs:
                la.append('r')

        action = sample_action(strategy, cur_player, state, bkt, la)
        state += action

        if action == 'f':
            if cur_player == 0: return -p0c
            else: return p1c

        elif action == 'c':
            deficit = abs(p0c - p1c)
            if cur_player==0: amt=min(deficit,p0s); p0c+=amt; p0s-=amt
            else: amt=min(deficit,p1s); p1c+=amt; p1s-=amt
            acted += 1
            round_over = p0c==p1c and (acted>=2 or last_was_raise)

            if round_over:
                if round_num == NUM_ROUNDS-1:
                    # Showdown
                    winner = lib.eval_showdown(h0, h1, board)
                    if winner == 0: return p1c
                    elif winner == 1: return -p0c
                    else: return 0.0
                else:
                    # Deal board cards for next round
                    round_num += 1
                    state += '/'
                    nb = NUM_BOARD[round_num]
                    for i in range(nb):
                        board_so_far[num_board_so_far] = board[num_board_so_far]
                        num_board_so_far += 1
                    cur_player = FIRST_PLAYER[round_num]
                    raises = 0
                    acted = 0
                    last_was_raise = False
                    continue

        elif action == 'r':
            rs = RAISE_SIZE[round_num]
            deficit = abs(p0c-p1c)
            if cur_player==0: amt=min(deficit+rs,p0s); p0c+=amt; p0s-=amt
            else: amt=min(deficit+rs,p1s); p1c+=amt; p1s-=amt
            raises += 1
            last_was_raise = True

        cur_player = 1 - cur_player

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('player_file')
    parser.add_argument('--hands', type=int, default=1000000)
    parser.add_argument('--seed', type=int, default=42)
    args = parser.parse_args()

    print("Loading engine...")
    lib = load_engine()
    print("Engine loaded.")

    print("Parsing strategy...")
    strategy = parse_strategy(args.player_file)
    print(f"  Loaded {len(strategy)} info sets")

    random.seed(args.seed)
    print(f"Simulating {args.hands:,} hands...")

    total_ev = 0.0
    for i in range(args.hands):
        total_ev += simulate_hand(strategy, lib)
        if i % 100000 == 0 and i > 0:
            print(f"  {i:,}/{args.hands:,} hands, P0 EV: {total_ev/i:.4f} chips/hand")

    avg_ev = total_ev / args.hands
    mbb_ev = (avg_ev / BB_SIZE) * 1000

    print(f"\n=== RESULTS ===")
    print(f"Hands: {args.hands:,}")
    print(f"P0 avg EV: {avg_ev:.6f} chips/hand")
    print(f"P0 avg EV: {mbb_ev:.2f} mbb/hand")
    print(f"Note: P0=SB, P1=BB. Symmetric stacks so Nash EV expected ~0.")

if __name__ == '__main__':
    main()
