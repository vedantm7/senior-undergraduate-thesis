#!/usr/bin/env python3
"""
interpolate_params.py
Reads raise/fold frequency results from calibration jobs and interpolates
to find the alpha and beta values that hit the empirical targets.

Targets (from HandHQ heads-up NLHE data, 2009):
  Maniac:  P1 preflop raise frequency = 0.70 (above P95 of observed distribution)
  Station: P1 preflop fold  frequency = 0.15 (below P10 of observed distribution)

Usage: python3 interpolate_params.py
"""
import os
import numpy as np

CALIB_DIR = "/home/mundhra.ve/poker_thesis/calibration"

# ── Targets ──────────────────────────────────────────────────────────────────
MANIAC_TARGET  = 0.70   # target raise frequency for maniac
STATION_TARGET = 0.15   # target fold frequency for station

def read_results(archetype):
    """
    Read raise_freq.txt files from each calibration subdirectory.
    Returns sorted list of (param_value, frequency) tuples.
    """
    results = []
    arch_dir = os.path.join(CALIB_DIR, archetype)
    if not os.path.exists(arch_dir):
        print(f"  WARNING: {arch_dir} does not exist")
        return results

    for subdir in os.listdir(arch_dir):
        freq_file = os.path.join(arch_dir, subdir, "raise_freq.txt")
        if not os.path.exists(freq_file):
            print(f"  Missing: {freq_file} (job may not be complete)")
            continue
        try:
            param_val = float(subdir)
            with open(freq_file) as f:
                for line in f:
                    # Line format: "P1 preflop raise frequency: 0.XXXX"
                    if "frequency:" in line:
                        freq = float(line.strip().split()[-1])
                        results.append((param_val, freq))
                        break
        except Exception as e:
            print(f"  Error reading {freq_file}: {e}")

    return sorted(results)

def interpolate(results, target):
    """
    Linear interpolation to find param value that hits target frequency.
    """
    if len(results) < 2:
        print(f"  Need at least 2 data points, have {len(results)}")
        return None

    params = np.array([r[0] for r in results])
    freqs  = np.array([r[1] for r in results])

    # Check if target is within range
    if target < freqs.min() or target > freqs.max():
        print(f"  WARNING: target {target:.3f} is outside observed range "
              f"[{freqs.min():.3f}, {freqs.max():.3f}]")
        print(f"  Extrapolating — consider adding more candidate values")

    # Find bracketing points
    calibrated = np.interp(target, freqs, params)
    return calibrated

def main():
    print("=" * 60)
    print("CALIBRATION RESULTS")
    print("=" * 60)

    # ── Maniac ────────────────────────────────────────────────────────────────
    print(f"\n--- MANIAC (target raise freq = {MANIAC_TARGET}) ---")
    maniac_results = read_results("maniac")

    if maniac_results:
        print(f"{'Alpha':>8}  {'Raise Freq':>12}")
        print("-" * 25)
        for param, freq in maniac_results:
            marker = " <-- target" if abs(freq - MANIAC_TARGET) < 0.02 else ""
            print(f"{param:>8.2f}  {freq:>12.4f}{marker}")

        alpha_calibrated = interpolate(maniac_results, MANIAC_TARGET)
        if alpha_calibrated is not None:
            print(f"\n  >>> Calibrated alpha = {alpha_calibrated:.4f}")
    else:
        print("  No results found yet.")

    # ── Station ───────────────────────────────────────────────────────────────
    print(f"\n--- STATION (target fold freq = {STATION_TARGET}) ---")
    station_results = read_results("station")

    if station_results:
        print(f"{'Beta':>8}  {'Fold Freq':>12}")
        print("-" * 25)

        # For station, raise_freq.txt actually records fold frequency
        # (see measure_raise_freq.py — we'll need to confirm this)
        for param, freq in station_results:
            marker = " <-- target" if abs(freq - STATION_TARGET) < 0.02 else ""
            print(f"{param:>8.2f}  {freq:>12.4f}{marker}")

        beta_calibrated = interpolate(station_results, STATION_TARGET)
        if beta_calibrated is not None:
            print(f"\n  >>> Calibrated beta = {beta_calibrated:.4f}")
    else:
        print("  No results found yet.")

    # ── Lambda ────────────────────────────────────────────────────────────────
    print(f"\n--- NIT ---")
    print(f"  lambda = 1.31 (Walasek, Mullett & Stewart 2024, meta-analysis)")
    print(f"  95% CI: [1.10, 1.53]")

    print("\n" + "=" * 60)

if __name__ == '__main__':
    main()
