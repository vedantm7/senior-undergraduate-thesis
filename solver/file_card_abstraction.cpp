#include "file_card_abstraction.hpp"
#include <dlfcn.h>

typedef void hand_indexer_t;
typedef bool (*fn_init_t)( uint32_t, const uint8_t[], hand_indexer_t* );
typedef long (*fn_index_t)( const hand_indexer_t*, const uint8_t* );
typedef void (*fn_free_t)( hand_indexer_t* );

#define INDEXER_BUF_SIZE 4096

static bool       s_ready  = false;
static void      *s_dlh    = nullptr;
static fn_init_t  s_init   = nullptr;
static fn_index_t s_index  = nullptr;
static fn_free_t  s_free   = nullptr;

/* 4 indexers matching poker-cfrm's ClusterCardAbstraction:
 *   round 0: {2}      preflop
 *   round 1: {2,3}    flop
 *   round 2: {2,4}    turn
 *   round 3: {2,5}    river
 */
static uint8_t s_ix_buf[4][INDEXER_BUF_SIZE];

void FileCardAbstraction::init_hand_indexer() {
  if( s_ready ) return;
  const char *so = "/home/mundhra.ve/poker_thesis/hand_index.so";
  s_dlh = dlopen( so, RTLD_LAZY );
  if( !s_dlh ) {
    fprintf( stderr, "FileCardAbstraction: dlopen failed: %s\n", dlerror() );
    exit(1);
  }
  s_init  = (fn_init_t)  dlsym( s_dlh, "hand_indexer_init" );
  s_index = (fn_index_t) dlsym( s_dlh, "hand_index_last" );
  s_free  = (fn_free_t)  dlsym( s_dlh, "hand_indexer_free" );
  if( !s_init || !s_index || !s_free ) {
    fprintf( stderr, "FileCardAbstraction: dlsym failed: %s\n", dlerror() );
    exit(1);
  }

  uint8_t c0[] = {2};
  uint8_t c1[] = {2, 3};
  uint8_t c2[] = {2, 4};
  uint8_t c3[] = {2, 5};

  memset( s_ix_buf, 0, sizeof(s_ix_buf) );
  if( !s_init( 1, c0, (hand_indexer_t*)s_ix_buf[0] ) ||
      !s_init( 2, c1, (hand_indexer_t*)s_ix_buf[1] ) ||
      !s_init( 2, c2, (hand_indexer_t*)s_ix_buf[2] ) ||
      !s_init( 2, c3, (hand_indexer_t*)s_ix_buf[3] ) ) {
    fprintf( stderr, "FileCardAbstraction: hand_indexer_init failed\n" );
    exit(1);
  }
  s_ready = true;
  fprintf( stderr, "FileCardAbstraction: hand_index.so ready\n" );
}

FileCardAbstraction::FileCardAbstraction( const char *path, int num_rounds )
  : m_num_rounds( num_rounds )
{
  memset( m_buckets, 0, sizeof(m_buckets) );
  memset( m_num_buckets_per_round, 0, sizeof(m_num_buckets_per_round) );
  memset( m_num_entries, 0, sizeof(m_num_entries) );

  FILE *f = fopen( path, "rb" );
  if( !f ) {
    fprintf( stderr, "FileCardAbstraction: cannot open '%s'\n", path );
    exit(1);
  }
  for( int r = 0; r < num_rounds; ++r ) {
    int32_t rnum, nent;
    fread( &rnum, 4, 1, f );
    fread( &nent, 4, 1, f );
    if( rnum != r || nent != HOLDEM_ENTRIES[r] ) {
      fprintf( stderr, "FileCardAbstraction: bad header round %d "
               "(got round=%d entries=%d)\n", r, rnum, nent );
      exit(1);
    }
    m_num_entries[r] = nent;
    m_buckets[r] = new uint32_t[nent];
    if( (int)fread( m_buckets[r], 4, nent, f ) != nent ) {
      fprintf( stderr, "FileCardAbstraction: short read round %d\n", r );
      exit(1);
    }
    uint32_t mx = 0;
    for( int i = 0; i < nent; ++i )
      if( m_buckets[r][i] > mx ) mx = m_buckets[r][i];
    m_num_buckets_per_round[r] = (int)mx + 1;
    fprintf( stderr, "  round %d: %d entries, %d buckets\n",
             r, nent, m_num_buckets_per_round[r] );
  }
  fclose(f);
  fprintf( stderr, "FileCardAbstraction: loaded OK\n" );
  /* Initialize hand indexer now, before threads start */
  init_hand_indexer();
}

FileCardAbstraction::~FileCardAbstraction() {
  for( int r = 0; r < m_num_rounds; ++r )
    delete[] m_buckets[r];
}

int FileCardAbstraction::num_buckets( const Game *game,
                                      const BettingNode *node ) const {
  return m_num_buckets_per_round[ node->get_round() ];
}

int FileCardAbstraction::num_buckets( const Game *game,
                                      const State &state ) const {
  return m_num_buckets_per_round[ state.round ];
}

int FileCardAbstraction::compute_hand_index( int round,
                                             const uint8_t hole_c[2],
                                             const uint8_t board_c[],
                                             int num_board ) const {
  init_hand_indexer();

  /* Card array layout matching poker-cfrm ClusterCardAbstraction:
   *   round 0: [hole0, hole1]
   *   round 1: [hole0, hole1, board0..2]   (5 cards)
   *   round 2: [hole0, hole1, board0..3]   (6 cards)
   *   round 3: [hole0, hole1, board0..4]   (7 cards)
   */
  uint8_t cards[7];
  cards[0] = hole_c[0];
  cards[1] = hole_c[1];
  for( int i = 0; i < num_board; ++i ) cards[2+i] = board_c[i];

  long idx = s_index( (const hand_indexer_t*)s_ix_buf[round], cards );
  if( idx < 0 || idx >= m_num_entries[round] ) {
    fprintf( stderr, "FileCardAbstraction: index %ld OOB round %d "
             "(max %d)\n", idx, round, m_num_entries[round] );
    exit(1);
  }
  return (int)idx;
}

int FileCardAbstraction::get_bucket( const Game *game,
                                     const BettingNode *node,
                                     const uint8_t board_cards[ MAX_BOARD_CARDS ],
                                     const uint8_t hole_cards[ MAX_PURE_CFR_PLAYERS ]
                                                              [ MAX_HOLE_CARDS ] ) const {
  int r = node->get_round();
  int nb = 0;
  for( int i = 0; i <= r; ++i ) nb += game->numBoardCards[i];
  int idx = compute_hand_index( r, hole_cards[0], board_cards, nb );
  return (int)m_buckets[r][idx];
}

void FileCardAbstraction::precompute_buckets( const Game *game,
                                              hand_t &hand ) const {
  for( int r = 0; r < m_num_rounds; ++r ) {
    int nb = 0;
    for( int i = 0; i <= r; ++i ) nb += game->numBoardCards[i];
    for( int p = 0; p < game->numPlayers; ++p ) {
      int idx = compute_hand_index( r, hand.hole_cards[p],
                                    hand.board_cards, nb );
      hand.precomputed_buckets[p][r] = (int)m_buckets[r][idx];
    }
  }
}
