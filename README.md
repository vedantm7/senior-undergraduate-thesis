# Can Skill Substitute for Capital?
## Behavioral Distortions and Stack Asymmetry in Heads-Up Limit Texas Hold'em

**Vedant Mundhra** | Northeastern University | Senior Thesis | April 2026
Advised by Professor James Dana

## Overview

This repository contains all code, solver modifications, game definitions, and results for my senior undergraduate thesis. The paper uses Counterfactual Regret Minimization (CFR) to analyze how capital constraints and behavioral distortions interact in heads-up limit Texas Hold'em poker as a framework for studying competitive zero-sum environments with heterogeneous players.

## Research Question

Which suboptimal strategies are the most exploitable at different asymmetric stack depths?

## Repository Structure

solver/         Modified open-pure-cfr-buckets C++ solver
                Key modifications:
                - FileCardAbstraction: loads pre-generated bucket files
                - Modified utility functions: maniac, calling station, nit
                - Action tracking: p1_raises, p1_folds per hand

scripts/        Python analysis scripts
                - simulate_holdem.py     Nash EV measurement via Monte Carlo
                - measure_raise_freq.py  Action frequency measurement
                - check_convergence.py   Strategy convergence checking
                - interpolate_params.py  Utility parameter calibration
                - holdem_engine.c        C engine for hand evaluation
                - convert_abs.py         Abstraction file format conversion
                - card_abstraction.py    Python abstraction loader

gamedefs/       ACPC-format game definition files
                - holdem.limit.2p.{36_36,18_36,12_36,9_36}.game
                - *.reverse.game variants for DiD identification
                - kuhn.limit.2p.game and leduc.limit.2p.game for testing

abstractions/   Card abstraction generation scripts
                Note: holdem_100b_cfrm.abs (528MB) not included

slurm/          SLURM job scripts for Northeastern Explorer cluster
                - calibration/  Parameter sweep jobs
                - essay2/       Production experiment jobs

results/        Final converged strategy files (.player format)
                - baseline/     255B iteration Nash baseline (36v36)
                - essay2/       All experimental configurations

## Key Results (mbb/hand, net of positional effects)

Player 1 Type        | 36v36   | 18v36   | 12v36   | 9v36
---------------------|---------|---------|---------|------
Nash                 | -73.40  | -34.21  | -33.64  | -48.49
Calling Station b=5  | +117.99 | -1.44   | -65.30  | -1.99
Maniac a=5           | +205.98 | +184.08 | +44.65  | excl.

## Computational Details

- Solver: open-pure-cfr-buckets (Pure CFR, Gibson 2012)
- Card abstraction: 100 buckets/street via OCHS clustering (poker-cfrm)
- Baseline solve: 255 billion iterations, ~5 days, Northeastern Explorer cluster
- Convergence: 0.075% avg action probability change
- Nash EV: 5 million Monte Carlo hands per configuration

## Dependencies

- GCC with Boost libraries
- Python 3.13+ with numpy
- Northeastern Explorer cluster (SLURM) or equivalent

## Citation

Mundhra, V. (2026). Can Skill Substitute for Capital? Behavioral Distortions and
Stack Asymmetry in Heads-Up Limit Texas Hold'em. Senior Thesis, Northeastern University.
