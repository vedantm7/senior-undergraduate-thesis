#ifndef FILE_CARD_ABSTRACTION_HPP
#define FILE_CARD_ABSTRACTION_HPP

#include "card_abstraction.hpp"
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>

static const int HOLDEM_ENTRIES[4] = { 169, 1286792, 13960050, 123156254 };

class FileCardAbstraction : public CardAbstraction {
public:
  FileCardAbstraction( const char *abs_filepath, int num_rounds );
  virtual ~FileCardAbstraction();

  virtual int num_buckets( const Game *game,
                           const BettingNode *node ) const;
  virtual int num_buckets( const Game *game,
                           const State &state ) const;
  virtual int get_bucket( const Game *game,
                          const BettingNode *node,
                          const uint8_t board_cards[ MAX_BOARD_CARDS ],
                          const uint8_t hole_cards[ MAX_PURE_CFR_PLAYERS ]
                                                   [ MAX_HOLE_CARDS ] ) const;
  virtual bool can_precompute_buckets( ) const { return true; }
  virtual void precompute_buckets( const Game *game, hand_t &hand ) const;

private:
  int m_num_rounds;
  int m_num_buckets_per_round[MAX_ROUNDS];
  int m_num_entries[MAX_ROUNDS];
  uint32_t *m_buckets[MAX_ROUNDS];

  int compute_hand_index( int round,
                          const uint8_t hole_c[2],
                          const uint8_t board_c[],
                          int num_board ) const;
  static void init_hand_indexer();
};

#endif
