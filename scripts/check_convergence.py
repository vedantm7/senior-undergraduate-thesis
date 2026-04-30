#!/usr/bin/env python3
"""
Convergence check: compare strategy between two checkpoints.
Measures average change in action probabilities across all info sets.
"""
import sys, subprocess, re

PRINT_STRATEGY = "/home/mundhra.ve/poker_thesis/open-pure-cfr-buckets/print_player_strategy"

def parse_strategy(player_file):
    result = subprocess.run([PRINT_STRATEGY, player_file, "--max-round=4"],
                            capture_output=True, text=True)
    strategy = {}
    cur_player, cur_state = None, None
    for line in result.stdout.splitlines():
        m = re.match(r'=== PLAYER (\d+) ===', line)
        if m:
            cur_player = int(m.group(1)) - 1; continue
        m = re.match(r'STATE:(\S+)', line)
        if m:
            cur_state = m.group(1); continue
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

def compare_strategies(s1, s2):
    total_diff = 0.0
    count = 0
    max_diff = 0.0
    max_key = None
    for key in s1:
        if key not in s2:
            continue
        d1, d2 = s1[key], s2[key]
        all_actions = set(d1.keys()) | set(d2.keys())
        for a in all_actions:
            diff = abs(d1.get(a, 0.0) - d2.get(a, 0.0))
            total_diff += diff
            count += 1
            if diff > max_diff:
                max_diff = diff
                max_key = (key, a)
    avg_diff = total_diff / count if count > 0 else 0.0
    return avg_diff, max_diff, max_key

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print(f"Usage: {sys.argv[0]} <player_file_1> <player_file_2>")
        sys.exit(1)
    print(f"Loading {sys.argv[1]}...")
    s1 = parse_strategy(sys.argv[1])
    print(f"Loading {sys.argv[2]}...")
    s2 = parse_strategy(sys.argv[2])
    print(f"Comparing {len(s1)} vs {len(s2)} info sets...")
    avg_diff, max_diff, max_key = compare_strategies(s1, s2)
    print(f"\n=== CONVERGENCE CHECK ===")
    print(f"Avg action prob change: {avg_diff*100:.4f}%")
    print(f"Max action prob change: {max_diff*100:.4f}%")
    print(f"Max change at: {max_key}")
    print(f"\nInterpretation:")
    print(f"  <0.1% avg  -> well converged")
    print(f"  <1.0% avg  -> converging")
    print(f"  >1.0% avg  -> still far from convergence")
