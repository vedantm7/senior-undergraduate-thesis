/*
 * holdem_engine.c
 * Shared library for hold'em simulation.
 * Handles: card dealing, bucket lookup, hand evaluation.
 *
 * Compile:
 *   gcc -O2 -shared -fPIC -o holdem_engine.so holdem_engine.c \
 *       poker-cfrm/src/hand_index.c \
 *       -I poker-cfrm/include -lm
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <time.h>

/* hand_index interface */
typedef struct { uint32_t rounds; uint8_t _pad[8200]; } hand_indexer_t;
extern int  hand_indexer_init(uint32_t rounds, const uint8_t cpr[], hand_indexer_t *ix);
extern long hand_index_last(const hand_indexer_t *ix, const uint8_t cards[]);

/* Two Plus Two evaluator */
#define HANDRANKS_SIZE 32487834
static int HR[HANDRANKS_SIZE];
static int hr_loaded = 0;

static int eval7(int c0,int c1,int c2,int c3,int c4,int c5,int c6) {
    int p=HR[53+c0]; p=HR[p+c1]; p=HR[p+c2]; p=HR[p+c3];
    p=HR[p+c4]; p=HR[p+c5]; return HR[p+c6];
}
#define TPT(c) ((c)+1)

/* Bucket arrays per round */
static uint32_t *bkt[4] = {NULL,NULL,NULL,NULL};
static int       bkt_n[4] = {0,0,0,0};

/* Hand indexers: configs match poker-cfrm ClusterCardAbstraction */
static hand_indexer_t ix[4];
static int ix_ready = 0;

/* RNG */
static uint64_t rng_state = 0;
static uint32_t rng_next() {
    rng_state^=rng_state<<13; rng_state^=rng_state>>7; rng_state^=rng_state<<17;
    return (uint32_t)rng_state;
}

/* -----------------------------------------------------------------------
 * init(): load handranks and abstraction file
 * Returns 0 on success, -1 on error
 * ---------------------------------------------------------------------- */
int engine_init(const char *handranks_path, const char *abs_path) {
    /* Load handranks */
    if (!hr_loaded) {
        FILE *f = fopen(handranks_path, "rb");
        if (!f) { fprintf(stderr,"Cannot open %s\n",handranks_path); return -1; }
        fread(HR, sizeof(int), HANDRANKS_SIZE, f);
        fclose(f);
        hr_loaded = 1;
        fprintf(stderr,"Handranks loaded.\n");
    }

    /* Init hand indexers */
    if (!ix_ready) {
        uint8_t c0[]={2}, c1[]={2,3}, c2[]={2,4}, c3[]={2,5};
        if (!hand_indexer_init(1,c0,&ix[0]) ||
            !hand_indexer_init(2,c1,&ix[1]) ||
            !hand_indexer_init(2,c2,&ix[2]) ||
            !hand_indexer_init(2,c3,&ix[3])) {
            fprintf(stderr,"hand_indexer_init failed\n"); return -1;
        }
        ix_ready = 1;
        fprintf(stderr,"Hand indexers ready.\n");
    }

    /* Load abstraction file */
    FILE *f = fopen(abs_path,"rb");
    if (!f) { fprintf(stderr,"Cannot open %s\n",abs_path); return -1; }
    for (int r=0; r<4; r++) {
        int32_t rnum, nent;
        fread(&rnum,4,1,f); fread(&nent,4,1,f);
        if (bkt[r]) free(bkt[r]);
        bkt[r] = (uint32_t*)malloc((long)nent*4);
        if (!bkt[r]) { fprintf(stderr,"OOM round %d\n",r); return -1; }
        fread(bkt[r],4,nent,f);
        bkt_n[r] = nent;
        fprintf(stderr,"Round %d: %d entries loaded.\n",r,nent);
    }
    fclose(f);

    rng_state = (uint64_t)time(NULL);
    return 0;
}

/* -----------------------------------------------------------------------
 * get_bucket(round, hole0, hole1, board_cards, num_board)
 * Returns bucket id for the given hand at the given round.
 * hole0, hole1: ACPC card encoding (rank*4+suit)
 * board_cards: array of board cards dealt so far
 * ---------------------------------------------------------------------- */
int get_bucket(int round, int hole0, int hole1,
               const uint8_t *board, int num_board) {
    uint8_t cards[7];
    cards[0] = (uint8_t)hole0;
    cards[1] = (uint8_t)hole1;
    for (int i=0; i<num_board; i++) cards[2+i] = board[i];
    long idx = hand_index_last(&ix[round], cards);
    if (idx < 0 || idx >= bkt_n[round]) return 0;
    return (int)bkt[round][idx];
}

/* -----------------------------------------------------------------------
 * deal_hand(): deal a random hold'em hand
 * Output arrays must be pre-allocated:
 *   hole[2] = P0 hole cards
 *   hole1[2] = P1 hole cards
 *   board[5] = board cards
 * ---------------------------------------------------------------------- */
void deal_hand(uint8_t *h0, uint8_t *h1, uint8_t *board) {
    int deck[52];
    for (int i=0;i<52;i++) deck[i]=i;
    /* Fisher-Yates for 9 cards */
    for (int i=0;i<9;i++) {
        int j=i+rng_next()%(52-i);
        int tmp=deck[i]; deck[i]=deck[j]; deck[j]=tmp;
    }
    h0[0]=deck[0]; h0[1]=deck[1];
    h1[0]=deck[2]; h1[1]=deck[3];
    board[0]=deck[4]; board[1]=deck[5]; board[2]=deck[6];
    board[3]=deck[7]; board[4]=deck[8];
}

/* -----------------------------------------------------------------------
 * eval_showdown(): evaluate 7-card showdown
 * Returns: 0 if P0 wins, 1 if P1 wins, -1 if tie
 * ---------------------------------------------------------------------- */
int eval_showdown(const uint8_t *h0, const uint8_t *h1, const uint8_t *board) {
    int r0 = eval7(TPT(h0[0]),TPT(h0[1]),
                   TPT(board[0]),TPT(board[1]),TPT(board[2]),
                   TPT(board[3]),TPT(board[4]));
    int r1 = eval7(TPT(h1[0]),TPT(h1[1]),
                   TPT(board[0]),TPT(board[1]),TPT(board[2]),
                   TPT(board[3]),TPT(board[4]));
    if (r0 > r1) return 0;
    if (r1 > r0) return 1;
    return -1;
}
