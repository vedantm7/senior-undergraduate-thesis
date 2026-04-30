#ifndef __PURE_CFR_HAND_HPP__
#define __PURE_CFR_HAND_HPP__

/* 
 * hand.hpp
 * Richard Gibson, Jun 28, 2013
 *
 * Structure to represent a hand with possible precomputed buckets and
 * showdown info.
 *
 * Copyright (C) 2013 by Richard Gibson
 */

/* C / C++ / STL includes */

/* C project_acpc_server includes */
extern "C" {
}

/* Pure CFR includes */
#include "constants.hpp"

typedef struct {
  /* The actual cards for this hand */
  uint8_t board_cards[ MAX_BOARD_CARDS ];
  uint8_t hole_cards[ MAX_PURE_CFR_PLAYERS ][ MAX_HOLE_CARDS ];
  /* When bucketing is only dependent on the round,
   * we just compute the buckets once and store
   */
  int precomputed_buckets[ MAX_PURE_CFR_PLAYERS ][ MAX_ROUNDS ];
  /* Action history for modified utility functions (Essay 2) */
  mutable int p1_raises;  /* number of raises taken by player 1 this hand */
  mutable int p1_folds;   /* number of folds taken by player 1 this hand */
  union {
    /* Potsize divided by pot_frac_recip[ p ][ type ] = utilily for player p
     * (>2p only)
     */
    int pot_frac_recip[ MAX_PURE_CFR_PLAYERS ][ LEAF_NUM_TYPES ];
    /* (-1,0,1) if player (loses,ties,wins) in showdown (2p only)*/
    int8_t showdown_value_2p[ 2 ]; 
  } eval;
} hand_t;

#endif
