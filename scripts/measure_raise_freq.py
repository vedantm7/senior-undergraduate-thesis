#!/usr/bin/env python3
import sys, subprocess, re, argparse

PRINT_STRATEGY = "/home/mundhra.ve/poker_thesis/open-pure-cfr-buckets/print_player_strategy"

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('player_file')
    args = parser.parse_args()

    result = subprocess.run([PRINT_STRATEGY, args.player_file],
                            capture_output=True, text=True)

    cur_player = None
    cur_state  = None

    total_raise_prob = 0.0
    total_fold_prob  = 0.0
    total_buckets    = 0

    preflop_raise_prob = 0.0
    preflop_fold_prob  = 0.0
    preflop_buckets    = 0

    for line in result.stdout.splitlines():
        m = re.match(r'=== PLAYER (\d+) ===', line)
        if m:
            cur_player = int(m.group(1)) - 1
            continue

        m = re.match(r'STATE:(\S+)', line)
        if m:
            cur_state = m.group(1)
            continue

        if cur_player != 1 or cur_state is None:
            continue

        m = re.match(r'\s+Bucket (\d+): (.+)', line)
        if m:
            actions = {}
            for part in m.group(2).split():
                pm = re.match(r'([\d.e+\-]+)%([fcr])', part)
                if pm:
                    actions[pm.group(2)] = float(pm.group(1)) / 100.0

            r = actions.get('r', 0.0)
            f = actions.get('f', 0.0)

            total_raise_prob += r
            total_fold_prob  += f
            total_buckets    += 1

            if '/' not in cur_state:
                preflop_raise_prob += r
                preflop_fold_prob  += f
                preflop_buckets    += 1

    if total_buckets == 0:
        print("ERROR: No buckets found for player 1")
        sys.exit(1)

    print(f"Total buckets (all streets):  {total_buckets}")
    print(f"Preflop buckets:              {preflop_buckets}")
    print(f"P1 all-streets raise freq:    {total_raise_prob / total_buckets:.4f}")
    print(f"P1 all-streets fold  freq:    {total_fold_prob  / total_buckets:.4f}")
    print(f"P1 preflop raise freq:        {preflop_raise_prob / preflop_buckets:.4f}")
    print(f"P1 preflop fold  freq:        {preflop_fold_prob  / preflop_buckets:.4f}")

if __name__ == '__main__':
    main()
