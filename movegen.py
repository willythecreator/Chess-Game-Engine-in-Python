from move import Move
from board import rank_of

KNIGHT_ATTACKS = [0] * 64
KING_ATTACKS = [0] * 64
PAWN_ATTACKS = {'w': [0] * 64, 'b': [0] * 64}

KNIGHT_OFFSETS = [
    (2, 1), (2, -1), (-2, 1), (-2, -1),
    (1, 2), (1, -2), (-1, 2), (-1, -2)
]

KING_OFFSETS = [
    (1, 0), (-1, 0), (0, 1), (0, -1),
    (1, 1), (1, -1), (-1, 1), (-1, -1),
]

def in_bounds(f, r):
    return 0 <= f < 8 and 0 <= r < 8

for sq in range(64):
    f, r = sq % 8, sq // 8

    # Knight
    for df, dr in KNIGHT_OFFSETS:
        nf, nr = f + df, r + dr
        if in_bounds(nf, nr):
            KNIGHT_ATTACKS[sq] |= 1 << (nr * 8 + nf)

    # King
    for df, dr in KING_OFFSETS:
        nf, nr = f + df, r + dr
        if in_bounds(nf, nr):
            KING_ATTACKS[sq] |= 1 << (nr * 8 + nf)

    # Pawn attacks
    # WHite pawns capture upward (rank+1), Black pawns capture downward (rank-1)
    for df in (-1, 1):
        # White
        wf, wr = f + df, r + 1
        if in_bounds(wf, wr):
            PAWN_ATTACKS['w'][sq] |= 1 << (wr * 8 + wf)

        # Black
        bf, br = f + df, r - 1
        if in_bounds(bf, br):
            PAWN_ATTACKS['b'][sq] |= 1 << (br * 8 + bf)

DIRECTIONS = {
    'rook': [(1, 0), (-1, 0), (0, 1), (0, -1)],
    'bishop': [(1, 1), (1, -1), (-1, 1), (-1, -1)],
}

def slider_attacks(sq, occupancy, deltas):
    f, r = sq % 8, sq // 8
    attacks = 0
    for df, dr in deltas:
        nf, nr = f + df, r + dr
        while in_bounds(nf, nr):
            target = nr * 8 + nf
            attacks |= 1 << target
            if occupancy & (1 << target):
                break
            nf += df
            nr += dr
    return attacks

def is_in_check(board, side):
    king_piece = 'K' if side == 'w' else 'k'
    bb = board.bitboards[king_piece]
    if bb == 0:
        return False
    king_sq = (bb & -bb).bit_length() - 1
    enemy = 'b' if side == 'w' else 'w'
    occ = board.all_occupied()

    enemy_n = 'N' if enemy == 'w' else 'n'
    if KNIGHT_ATTACKS[king_sq] & board.bitboards[enemy_n]:
        return True

    enemy_k = 'K' if enemy == 'w' else 'k'
    if KING_ATTACKS[king_sq] & board.bitboards[enemy_k]:
        return True

    enemy_p = 'P' if enemy == 'w' else 'p'
    if PAWN_ATTACKS[side][king_sq] & board.bitboards[enemy_p]:
        return True

    enemy_r = 'R' if enemy == 'w' else 'r'
    enemy_q = 'Q' if enemy == 'w' else 'q'
    if slider_attacks(king_sq, occ, DIRECTIONS['rook']) & (board.bitboards[enemy_r] | board.bitboards[enemy_q]):
        return True

    enemy_b = 'B' if enemy == 'w' else 'b'
    if slider_attacks(king_sq, occ, DIRECTIONS['bishop']) & (board.bitboards[enemy_b] | board.bitboards[enemy_q]):
        return True

    return False

def apply_move_temp(board, move):
    # Apply a move and return the modified bitboards + ep + side so we can undo
    bbs = {k: v for k, v in board.bitboards.items()}
    piece = move.piece

    bbs[piece] &= ~(1 << move.from_sq)

    if move.captured:
        bbs[move.captured] &= ~(1 << move.to_sq)
        
    if move.en_passant:
        ep_dir = -8 if board.side == 'w' else 8
        ep_victim = 'p' if board.side == 'w' else 'P'
        bbs[ep_victim] &= ~(1 << (move.to_sq + ep_dir))

    target = move.promotion if move.promotion else piece
    bbs[target] |= 1 << move.to_sq

    return bbs

def _sq_attacked_by(board, sq, side):
    return is_in_check_sq(board, sq, side)

def is_in_check_sq(board, sq, side):
    enemy = 'b' if side == 'w' else 'w'
    occ = board.all_occupied()

    enemy_n = 'N' if enemy == 'w' else 'n'
    if KNIGHT_ATTACKS[sq] & board.bitboards[enemy_n]:
        return True
    enemy_k = 'K' if enemy == 'w' else 'k'
    if KING_ATTACKS[sq] & board.bitboards[enemy_k]:
        return True
    enemy_p = 'P' if enemy == 'w' else 'p'
    if PAWN_ATTACKS[side][sq] & board.bitboards[enemy_p]:
        return True
    enemy_r = 'R' if enemy == 'w' else 'r'
    enemy_q = 'Q' if enemy == 'w' else 'q'
    if slider_attacks(sq, occ, DIRECTIONS['rook']) & (board.bitboards[enemy_r] | board.bitboards[enemy_q]):
        return True
    enemy_b = 'B' if enemy == 'w' else 'b'
    if slider_attacks(sq, occ, DIRECTIONS['bishop']) & (board.bitboards[enemy_b] | board.bitboards[enemy_q]):
        return True
    return False

def generate_moves(board):
    moves = []
    side = board.side
    enemy = 'b' if side == 'w' else 'w'
    own_occ = board.occupied(side)
    enemy_occ = board.occupied(enemy)
    all_occ = own_occ | enemy_occ

    # Loop through each piece type for this side
    for piece_char in ('P', 'N', 'B', 'R', 'Q', 'K') if side == 'w' else ('p', 'n', 'b', 'r', 'q', 'k'):
        bb = board.bitboards[piece_char]
        while bb:
            from_sq = (bb & -bb).bit_length() - 1
            bb &= bb - 1

            if piece_char.upper() == 'N':
                targets = KNIGHT_ATTACKS[from_sq] & ~own_occ
                while targets:
                    to_sq = (targets & -targets).bit_length() - 1
                    targets &= targets - 1
                    captured = None
                    if enemy_occ & (1 << to_sq):
                        for ep, eb in board.bitboards.items():
                            if (eb >> to_sq) & 1:
                                captured = ep
                                break
                    moves.append(Move(from_sq, to_sq, piece_char, captured))

            elif piece_char.upper() == 'P':
                direction = 1 if side == 'w' else -1
                start_rank = 1 if side == 'w' else 6
                prom_rank = 6 if side == 'w' else 1

                to_sq = from_sq + 8 * direction
                if not (all_occ & (1 << to_sq)):
                    if rank_of(from_sq) == prom_rank:
                        for prom in ('Q', 'R', 'B', 'N') if side == 'w' else ('q', 'r', 'b', 'n'):
                            moves.append(Move(from_sq, to_sq, piece_char, promotion=prom))
                    else:
                        moves.append(Move(from_sq, to_sq, piece_char,
                                          double_push=abs(rank_of(from_sq) - start_rank) == 1))
                    if rank_of(from_sq) == start_rank:
                        to_sq2 = from_sq + 16 * direction
                        if not (all_occ & (1 << to_sq2)):
                            moves.append(Move(from_sq, to_sq2, piece_char, double_push=True))

                pawn_caps = PAWN_ATTACKS[side][from_sq]
                targets = pawn_caps & enemy_occ
                while targets:
                    to_sq = (targets & -targets).bit_length() - 1
                    targets &= targets - 1
                    captured = None
                    for ep, eb in board.bitboards.items():
                        if (eb >> to_sq) & 1:
                            captured = ep
                            break
                    if rank_of(from_sq) == prom_rank:
                        for prom in ('Q', 'R', 'B', 'N') if side == 'w' else ('q','r','b','n'):
                            moves.append(Move(from_sq, to_sq, piece_char, captured, promotion=prom))
                    else:
                        moves.append(Move(from_sq, to_sq, piece_char, captured))

                if board.ep != -1:
                    ep_caps = pawn_caps & (1 << board.ep)
                    if ep_caps:
                        moves.append(Move(from_sq, board.ep, piece_char, en_passant=True))

            elif piece_char.upper() in ('B', 'R', 'Q'):
                if piece_char.upper() == 'B':
                    deltas = DIRECTIONS['bishop']
                elif piece_char.upper() == 'R':
                    deltas = DIRECTIONS['rook']
                else:
                    deltas = DIRECTIONS['bishop'] + DIRECTIONS['rook']
                targets = slider_attacks(from_sq, all_occ, deltas) & ~own_occ
                while targets:
                    to_sq = (targets & -targets).bit_length() - 1
                    targets &= targets - 1
                    captured = None
                    if enemy_occ & (1 << to_sq):
                        for ep, eb in board.bitboards.items():
                            if (eb >> to_sq) & 1:
                                captured = ep
                                break
                    moves.append(Move(from_sq, to_sq, piece_char, captured))

            # Castling
            elif piece_char.upper() == 'K':
                targets = KING_ATTACKS[from_sq] & ~own_occ 
                while targets:
                    to_sq = (targets & -targets).bit_length() - 1
                    targets &= targets - 1
                    captured = None
                    if enemy_occ & (1 << to_sq):
                        for ep, eb in board.bitboards.items():
                            if (eb >> to_sq) & 1:
                                captured = ep
                                break
                    moves.append(Move(from_sq, to_sq, piece_char, captured))

            # Castling rights: bit 3=K, 2=Q, 1=k, 0=q
            if piece_char == 'K' and from_sq == 4: # white king on e1
                occ = all_occ

                # Kingside
                if board.castling & 0b1000:
                    if not ( occ & ((1 << 5) | (1<<6))):
                        if not is_in_check(board, 'w'):
                            if not _sq_attacked_by(board, 5, 'w') and not _sq_attacked_by(board, 6, 'w'):
                                moves.append(Move(4, 6, 'K', castling=True))

                # Queenside
                if board.castling & 0b0100:
                    if not (occ & ((1<<1)|(1<<2)|(1<<3))):
                        if not is_in_check(board, 'w'):
                            if not _sq_attacked_by(board, 3, 'w') and not _sq_attacked_by(board, 2, 'w'):
                                moves.append(Move(4, 2, 'K', castling=True))

            if piece_char == 'k' and from_sq == 60: # black king on e8
                occ = all_occ

                # Kingside
                if board.castling & 0b0010:
                    if not (occ & ((1<<61)|(1<<62))):
                        if not is_in_check(board, 'b'):
                            if not _sq_attacked_by(board, 61, 'b') and not _sq_attacked_by(board, 62, 'b'):
                                moves.append(Move(60, 62, 'k', castling=True))

                # Queenside
                if board.castling & 0b0001:
                    if not (occ & ((1<<57)|(1<<58)|(1<<59))):
                        if not is_in_check(board, 'b'):
                            if not _sq_attacked_by(board, 59, 'b') and not _sq_attacked_by(board, 58, 'b'):
                                moves.append(Move(60, 58, 'k', castling=True))

    # Filter: remove moves that leave own king in check
    legal = []
    for move in moves:
        saved_bbs = {k: v for k, v in board.bitboards.items()}
        saved_ep = board.ep
        saved_side = board.side

        # Apply move temporarily
        new_bbs = apply_move_temp(board, move)
        board.bitboards = new_bbs
        board.side = enemy if side == 'w' else 'w' # flip to check from side's perspective

        # Check if own king is still in check after the move
        board.side = side
        still_in_check = is_in_check(board, side)

        # Restore
        board.bitboards = saved_bbs
        board.ep = saved_ep
        board.side = saved_side

        if not still_in_check:
            legal.append(move)

    return legal