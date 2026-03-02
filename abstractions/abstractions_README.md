# Game Abstractions

## Overview

Solving heads-up limit Texas Hold'em requires abstractions to reduce the ~10^13-10^14 state space to computationally tractable size. This document describes the three abstractions employed in our asymmetric stack analysis.

## 1. Suit Isomorphism

### Definition
Lossless abstraction exploiting suit symmetry in poker. Hands differing only by suit permutation are strategically equivalent and can be merged into a single information set.

### Technical Details
- **Preflop**: Maps 1,326 hand combinations → 169 canonical hands
- **Implementation**: Built into OpenSpiel poker games
- **Example**: {A♠K♠, A♥K♥, A♦K♦, A♣K♣} → single infoset "AKs"
- **Loss**: Zero (provably lossless per Gilpin & Sandholm 2007)

### Why Necessary
Free 8x state space reduction with no strategic information loss. Standard practice in all poker solvers.

---

## 2. Card Bucketing (Hand Abstraction)

### Definition
Lossy abstraction clustering strategically similar hand-board combinations into buckets based on Expected Hand Strength (EHS) and potential to improve.

### Technical Details
- **Method**: k-means clustering with Earth Mover's Distance (EMD)
- **Buckets per round**: 100 (flop, turn, river)
- **Preflop**: Uses suit isomorphism (no bucketing)
- **Total abstractions**: ~100^3 = 10^6 post-flop states (vs. millions unbucketed)
- **Implementation**: Generated offline via poker-cfrm, loaded into OpenSpiel
- **Loss**: Lossy—hands in same bucket not perfectly equivalent

### Clustering Features
For each hand-board combination, compute:
- **EHS**: P(win | opponent has random hand)
- **Hand Potential**: Distribution of equity improvements on future streets
- **Distance Metric**: EMD between equity distributions

### Why Necessary
Without bucketing, post-flop state space is intractable:
- Flop: ~25,000 hand-board combinations per player
- Turn: ~50,000 combinations
- River: ~100,000 combinations

100 buckets reduces this by 250-1000x.

### Example
```
Flop: K♥7♦2♣

Bucket 12 (Overpairs):
- A♠A♣, Q♥Q♦, J♠J♥

Bucket 18 (Top pair strong kicker):
- K♠Q♥, K♦J♣, K♣T♠

Bucket 47 (Weak pairs):
- 7♠6♦, 2♥2♠

Bucket 89 (Air):
- 9♠8♦, 6♣5♥, J♠T♦
```

All hands in bucket 18 use identical strategy despite slight equity differences.

### Implementation Notes
Generated using:
```bash
./cluster-abs \
  --save-to holdem_100b.abs \
  --buckets 1,100,100,100 \
  --metric mixed_nooo \
  --nb-samples 0,1000,1000,1000 \
  --threads 32
```

Output is binary file mapping hand_index → bucket_id for each round.

---

## 3. Betting Cap

### Definition
Lossy abstraction limiting maximum raises per betting round to 3 (vs. standard 4 in limit poker).

### Technical Details
- **Standard limit**: bet → raise → reraise → cap (4 bet sequence)
- **Our abstraction**: bet → raise → reraise (3 bet sequence, then must call/fold)
- **Implementation**: Modify OpenSpiel game rules or post-process to exclude 4+ bet sequences
- **Loss**: Lossy—eliminates rare but legitimate strategic lines

### Why Necessary
Each additional raise level multiplies game tree size. Betting cap provides substantial complexity reduction:
- Reduces tree depth
- Empirically affects <1% of hands (deep betting sequences rare)
- Similar to Zinkevich et al. (2007) who used 3-bet cap in foundational CFR paper

### Example
```
Standard limit sequence (allowed):
P1: bet $2
P2: raise to $4  (1st raise)
P1: raise to $6  (2nd raise)
P2: raise to $8  (3rd raise)
P1: raise to $10 (4th raise, "cap")
P2: call $10

Our abstraction (forced):
P1: bet $2
P2: raise to $4
P1: raise to $6
P2: raise to $8
P1: MUST call or fold (cannot raise 4th time)
```

### Justification
Analysis of online poker databases shows:
- 3-bet sequences: ~5-10% of hands
- 4-bet sequences: <1% of hands
- 5+ bet sequences: <0.1% of hands

Strategic impact minimal while computational savings substantial.

---

## Why Bet Sizing Abstraction is Unnecessary

**In no-limit poker**, bet sizing discretization is critical because players can bet any amount from minimum bet to all-in—a continuous action space requiring abstraction to discrete sizes (e.g., 0.5× pot, 1× pot, all-in). Tartanian (Gilpin et al., 2008) pioneered this approach for no-limit games.

**In limit poker**, the betting structure is already discrete by design. All bets are fixed amounts: \$2 on preflop/flop, \$4 on turn/river in a \$2/\$4 game. The action space is naturally discrete: {fold, call, raise fixed amount, check}. No abstraction needed—the game rules already provide the discretization that no-limit solvers must artificially impose.

---

## Abstraction Summary

| Abstraction | Type | Built-in? | Reduction Factor | Information Loss |
|-------------|------|-----------|------------------|------------------|
| Suit Isomorphism | Lossless | Yes | ~8× | None |
| Card Bucketing | Lossy | No | 250-1000× | Minimal (if bucketed well) |
| Betting Cap | Lossy | No | ~10-50× | <1% of hands affected |
| **Combined** | **Lossy** | **Partial** | **~20,000×** | **Acceptable for research** |

**Total state space reduction**: From ~10^14 states to ~10^9-10^10 tractable states.

---

## References
- Gilpin, A., & Sandholm, T. (2007). Lossless abstraction of imperfect information games. *AAAI*.
- Gilpin, A., Sandholm, T., & Sørensen, T. B. (2008). A heads-up no-limit Texas Hold'em poker player. *AAMAS*.
- Zinkevich, M., et al. (2007). Regret minimization in games with incomplete information. *NIPS*.
- Bowling, M., et al. (2015). Heads-up limit hold'em poker is solved. *Science*.

---

## Implementation Files

(To be added: Bucket generation code, abstraction files, loading utilities)


---

## Implementation Details

### Generated Abstraction File
`holdem_100b.abs` (528MB) is tracked via Git LFS and stored in this directory. It maps every possible hand-board combination at every street to a bucket ID (0-99).

### Cluster Environment
All computation was performed on the Northeastern Discovery Cluster.
- **Node:** `d0073`, `short` partition
- **Resources:** 32 CPUs, 64GB RAM
- **Compiler:** gcc/11.1.0, boost/1.80.0
- **Repo:** `github.com/pandaant/poker-cfrm`
- **Location on cluster:** `/home/mundhra.ve/poker_thesis/`

### Prerequisites (Not Stored in Repo)

Two large prerequisite files are required to regenerate the abstraction but are not stored in this repository due to size constraints.

**1. handranks.dat (124MB)**

A precomputed lookup table for O(1) poker hand evaluation (TwoPlusTwo evaluator).

To obtain:
```bash
git clone https://github.com/christophschmalhofer/poker.git
cp poker/XPokerEval/XPokerEval.TwoPlusTwo/HandRanks.dat poker-cfrm/handranks.dat
```

**2. ehs.dat (528MB)**

A precomputed Expected Hand Strength table covering all hand-board combinations across all streets, generated via Monte Carlo simulation.

To regenerate (submit as a cluster job, takes ~2 hours at 16 threads):
```bash
cd poker-cfrm/tools/ehs_gen
make CXX=g++ CC=gcc
./gen_eval_table
mv ehs.dat ../../ehs.dat
```

### Compilation Notes

The `poker-cfrm` codebase requires two fixes for compatibility with gcc/11.1.0. The compound literal array syntax used throughout is rejected by the newer compiler. In the following files, replace all instances of:
```cpp
assert(hand_indexer_init(1, (uint8_t[]) {2}, &indexer[0]));
```
with:
```cpp
uint8_t _c0[] = {2};
assert(hand_indexer_init(1, _c0, &indexer[0]));
```
(and equivalently for the 3-, 4-, and 5-card variants)

Affected files: `include/ehs_lookup.hpp`, `include/abstraction_generator.hpp`, `include/card_abstraction.hpp`, `src/abstraction_generator.cpp`, `tools/ehs_gen/src/gen_eval_table.cpp`, `tools/ehs_gen/include/ehs_lookup.hpp`

Also add the Boost library path explicitly to the makefile `CPP_LIBRARIES` line:
```
-L/shared/centos7/boost/1.80.0/lib -lpthread -lboost_program_options
```

### Regenerating the Abstraction

Once prerequisites are in place and the repo is compiled:
```bash
./cluster-abs \
  --save-to holdem_100b.abs \
  --buckets 1,100,100,100 \
  --metric mixed_nooo \
  --nb-samples 0,1000,1000,1000 \
  --threads 32 \
  --handranks /path/to/handranks.dat
```

Runtime: ~40 minutes at 32 threads on the Discovery cluster.
