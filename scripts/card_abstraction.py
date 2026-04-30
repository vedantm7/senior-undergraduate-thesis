import ctypes
import struct
import os
import numpy as np

# ─── Load hand indexer shared library ────────────────────────────────────────

_lib_path = '/home/mundhra.ve/poker_thesis/hand_index.so'
_lib = ctypes.CDLL(_lib_path)

# hand_indexer_t structure (opaque, we just need enough space)
# From hand_index.h - allocate a large buffer for the struct
HAND_INDEXER_SIZE = 256 * 1024  # 256KB should be more than enough

class HandIndexer(ctypes.Structure):
    _fields_ = [('data', ctypes.c_uint8 * HAND_INDEXER_SIZE)]

# Function signatures
_lib.hand_indexer_init.restype = ctypes.c_bool
_lib.hand_indexer_init.argtypes = [
    ctypes.c_uint32,                    # rounds
    ctypes.POINTER(ctypes.c_uint8),     # cards_per_round
    ctypes.POINTER(HandIndexer)         # indexer
]

_lib.hand_index_last.restype = ctypes.c_uint64
_lib.hand_index_last.argtypes = [
    ctypes.POINTER(HandIndexer),        # indexer
    ctypes.POINTER(ctypes.c_uint8)      # cards
]

# ─── Initialize indexers for each round ──────────────────────────────────────

_indexers = []

def _init_indexers():
    # Preflop: 2 hole cards
    idx0 = HandIndexer()
    cards0 = (ctypes.c_uint8 * 1)(2)
    assert _lib.hand_indexer_init(1, cards0, ctypes.byref(idx0))
    _indexers.append(idx0)

    # Flop: 2 hole + 3 board
    idx1 = HandIndexer()
    cards1 = (ctypes.c_uint8 * 2)(2, 3)
    assert _lib.hand_indexer_init(2, cards1, ctypes.byref(idx1))
    _indexers.append(idx1)

    # Turn: 2 hole + 4 board
    idx2 = HandIndexer()
    cards2 = (ctypes.c_uint8 * 2)(2, 4)
    assert _lib.hand_indexer_init(2, cards2, ctypes.byref(idx2))
    _indexers.append(idx2)

    # River: 2 hole + 5 board
    idx3 = HandIndexer()
    cards3 = (ctypes.c_uint8 * 2)(2, 5)
    assert _lib.hand_indexer_init(2, cards3, ctypes.byref(idx3))
    _indexers.append(idx3)

_init_indexers()

# ─── Load bucket file ─────────────────────────────────────────────────────────

ROUND_SIZES = [169, 1286792, 13960050, 123156254]

def load_abstraction(abs_file):
    """Load holdem_100b.abs and return list of bucket arrays per round."""
    buckets = []
    with open(abs_file, 'rb') as f:
        for r in range(4):
            round_num = struct.unpack('<i', f.read(4))[0]
            nb_buckets = struct.unpack('<i', f.read(4))[0]
            data = np.frombuffer(f.read(4 * ROUND_SIZES[r]), dtype=np.uint32)
            buckets.append(data)
            print(f'Round {r}: {nb_buckets} buckets, {ROUND_SIZES[r]} indices loaded')
    return buckets

# ─── Card conversion ──────────────────────────────────────────────────────────

def openspiel_card_to_cfrm(card):
    """Convert OpenSpiel card integer to poker-cfrm card format.
    OpenSpiel: card = rank * num_suits + suit (rank 0-12, suit 0-3)
    poker-cfrm: card = rank * 4 + suit (same format)
    """
    return card  # same encoding

# ─── Main lookup function ─────────────────────────────────────────────────────

def get_bucket(hole_cards, board_cards, street, buckets):
    import sys
    all_cards = hole_cards + board_cards
    if len(all_cards) != len(set(all_cards)):
        return 0  # return safe default instead of crashing
    cards = (ctypes.c_uint8 * 7)()
    cards[0] = hole_cards[0]
    cards[1] = hole_cards[1]
    for i, c in enumerate(board_cards):
        cards[2 + i] = c
    index = _lib.hand_index_last(ctypes.byref(_indexers[street]), cards)
    return int(buckets[street][index])

# ─── Card string parsing ──────────────────────────────────────────────────────

RANK_MAP = {'2':0,'3':1,'4':2,'5':3,'6':4,'7':5,'8':6,'9':7,'T':8,'J':9,'Q':10,'K':11,'A':12}
SUIT_MAP = {'c':0,'d':1,'h':2,'s':3}

def card_str_to_int(card_str):
    """Convert '2c', 'Ah', etc to OpenSpiel card integer (rank*4 + suit)."""
    rank = RANK_MAP[card_str[0]]
    suit = SUIT_MAP[card_str[1]]
    return rank * 4 + suit

def get_board_cards_from_state(state):
    """Extract board cards from state by peeking at a child state."""
    if state.is_terminal() or state.is_chance_node():
        return []
    legal = state.legal_actions()
    if not legal:
        return []
    child = state.child(legal[0])
    for line in str(child).split('\n'):
        if 'ACPC State:' in line:
            after_state = line.split('STATE:')[1]
            parts = after_state.split(':')
            if len(parts) >= 3:
                cards_section = parts[2]
                if '/' in cards_section:
                    board_str = '/'.join(cards_section.split('/')[1:])
                    # Remove any trailing non-card chars
                    board_str = board_str.replace('/', '')
                    cards = [board_str[i:i+2] for i in range(0, len(board_str), 2)]
                    return [card_str_to_int(c) for c in cards if len(c)==2 and c[0] in RANK_MAP]
    return []

def get_hole_cards_from_state(state, player):
    """Extract hole cards for player from information state string."""
    info = state.information_state_string(player)
    # Format: [Private: 2d2c]
    import re
    match = re.search(r'Private: ([^\]]+)', info)
    if match:
        cards_str = match.group(1).strip()
        cards = [cards_str[i:i+2] for i in range(0, len(cards_str), 2)]
        return [card_str_to_int(c) for c in cards if len(c)==2 and c[0] in RANK_MAP]
    return []

def get_bucket_for_state(state, player, street, buckets):
    """Get bucket ID for current player's hand on current street."""
    hole = get_hole_cards_from_state(state, player)
    board = get_board_cards_from_state(state)
    if not hole:
        return 0
    return get_bucket(hole, board, street, buckets)


if __name__ == '__main__':
    print('Loading abstraction file...')
    buckets = load_abstraction('/home/mundhra.ve/poker_thesis/holdem_100b.abs')
    print('Done!')
    
    # Test: preflop bucket for Ace of spades + King of spades
    # OpenSpiel encoding: rank * 4 + suit
    ace_spades = 12 * 4 + 0   # rank 12 (Ace), suit 0 (spades)
    king_spades = 11 * 4 + 0  # rank 11 (King), suit 0 (spades)
    
    bucket = get_bucket([ace_spades, king_spades], [], 0, buckets)
    print(f'AKs preflop bucket: {bucket}')
    
    # Compare with a weaker hand
    two_seven = 0 * 4 + 0    # 2 of spades
    seven_off = 5 * 4 + 1    # 7 of hearts
    bucket2 = get_bucket([two_seven, seven_off], [], 0, buckets)
    print(f'27o preflop bucket: {bucket2}')
    
    print('AKs should have higher bucket than 27o (closer to 168)')

