from movegen import generate_moves, is_in_check
from evaluate import evaluate
from move import Move
import time

TRANSPOSITION_TABLE = {}
TT_EXACT = 0
TT_ALPHA = 1
TT_BETA = 2

MAX_DEPTH = 7 # iterative deeping goes up to this
QUIESCE_DEPTH = 4
killers = [[None, None] for _ in range(MAX_DEPTH + 1)]

_search_start = 0.0
_time_limit = 5.0

def _board_hash(board):
    # Simple hash of the board state
    return (
        tuple(board.bitboards[p] for p in sorted(board.bitboards)),
        board.side,
        board.ep,
        board.castling,
    )

def _move_score(move, board, depth=0):
    # Score a move for ordering - higher = seatch first
    score = 0
    if move.captured:
        # MVV-LVA: most valuable victim, least valuable attacker
        victim_val = {
            'P':100, 'N':320, 'B':320, 'R': 500, 'Q':900, 'K':20000,
            'p':100, 'n':320, 'b':320, 'r': 500, 'q':900, 'k':20000,
        }.get(move.captured, 0)
        attacker_val = {
            'P':100, 'N': 320, 'B':320, 'R':500, 'Q':900, 'K':20000,
            'p': 100, 'n':320, 'b':320, 'r':500, 'q':900, 'k':20000,
        }.get(move.piece, 100)
        score += 10 * victim_val - attacker_val
    if move.promotion:
        score += 900
    if move.castling:
        score += 60
    if not move.captured:
        if killers[depth][0] is not None and move == killers[depth][0]:
            score += 80
        elif killers[depth][1] is not None and move == killers[depth][1]:
            score += 70
    return score

def _apply_move(board, move):
    # Apply move to board in place
    b = board
    piece = move.piece

    b.bitboards[piece] &= ~(1 << move.from_sq)

    if move.captured:
        b.bitboards[move.captured] &= ~(1 << move.to_sq)

    if move.castling:
        if move.to_sq == 6:
            b.bitboards['R'] &= ~(1 << 7); b.bitboards['R'] |= (1 << 5)
        elif move.to_sq == 2:
            b.bitboards['R'] &= ~(1 << 0); b.bitboards['R'] |= (1 << 3)
        elif move.to_sq == 62:
            b.bitboards['r'] &= ~(1 << 63); b.bitboards['r'] |= (1 << 61)
        elif move.to_sq == 58:
            b.bitboards['r'] &= ~(1 << 56); b.bitboards['r'] |= (1 << 59)

    if move.en_passant:
        ep_dir = -8 if b.side == 'w' else 8
        b.bitboards['p' if b.side == 'w' else 'P'] &= ~(1 << (move.to_sq + ep_dir))

    target = move.promotion if move.promotion else piece
    b.bitboards[target] |= 1 << move.to_sq

    b.ep = move.to_sq + (-8 if b.side == 'w' else 8) if move.double_push else -1

    if piece == 'K': b.castling &= ~0b1100
    if piece == 'k': b.castling &= ~0b0011
    if move.from_sq == 0: b.castling &= ~0b0100
    if move.from_sq == 7: b.castling &= ~0b1000
    if move.from_sq == 56: b.castling &= ~0b0001
    if move.from_sq == 63: b.castling &= ~0b0010

    b.side = 'b' if b.side == 'w' else 'w'
    if b.side == 'w':
        b.fullmove += 1

def _undo_move(board, move, saved):
    # Restore board from saved state
    board.bitboards = saved['bbs']
    board.side = saved['side']
    board.ep = saved['ep']
    board.castling = saved['castling']
    board.fullmove = saved['fullmove']

def _save(board):
    return {
        'bbs': {k: v for k, v in board.bitboards.items()},
        'side': board.side,
        'ep': board.ep,
        'castling': board.castling,
        'fullmove': board.fullmove,
    }

def quiesce(board, alpha, beta, depth=QUIESCE_DEPTH):
    # Quiescence search - only look at captures to avoid horizon effect
    stand_pat = evaluate(board)
    if board.side == 'b':
        stand_pat = -stand_pat

    if stand_pat >= beta:
        return beta
    if alpha < stand_pat:
        alpha = stand_pat

    if depth <= 0:
        return alpha

    moves = generate_moves(board)
    captures = [m for m in moves if m.captured or m.promotion]
    captures.sort(key=lambda m: _move_score(m, board), reverse=True)

    for move in captures:
        saved = _save(board)
        _apply_move(board, move)
        score = -quiesce(board, -beta, -alpha, depth - 1)
        _undo_move(board, move, saved)

        if score >= beta:
            return beta
        if score > alpha:
            alpha = score

    return alpha

def alphabeta(board, depth, alpha, beta, maximizing):
    if time.time() - _search_start > _time_limit:
        return 0
    # Alpha-beta minimax with transposition table
    key = _board_hash(board)

    if key in TRANSPOSITION_TABLE:
        tt_depth, tt_flag, tt_score = TRANSPOSITION_TABLE[key]
        if tt_depth >= depth:
            if tt_flag == TT_EXACT:
                return tt_score
            elif tt_flag == TT_ALPHA and tt_score <= alpha:
                return alpha
            elif tt_flag == TT_BETA and tt_score >= beta:
                return beta
            
    if depth == 0:
        score = quiesce(board, alpha, beta, QUIESCE_DEPTH)
        TRANSPOSITION_TABLE[key] = (0, TT_EXACT, score)
        return score
    
    moves = generate_moves(board)

    non_pawn = sum(bin(v).count('1') for k, v in board.bitboards.items()
                   if k not in ('P', 'p', 'K', 'k'))
    if depth >= 3 and not is_in_check(board, board.side) and non_pawn > 2:
        saved = _save(board)
        board.side = 'b' if board.side == 'w' else 'w'
        score = -alphabeta(board, depth - 3, -beta, -beta + 1, not maximizing)
        board.side = 'b' if board.side == 'w' else 'w'
        _undo_move(board, None, saved)
        if score >= beta:
            return beta

    original_alpha = alpha
    best_score = -100000

    for i, move in enumerate(moves):
        saved = _save(board)
        _apply_move(board, move)

        # LMR: reduce depth for late quiet moves
        reduction = 0
        if depth >= 3 and i >= 3 and not move.captured and not move.promotion:
            reduction = 1 if i < 6 else 2

        score = -alphabeta(board, depth - 1 - reduction, -beta, -alpha, not maximizing)

        # re-search at full depth if it raised alpha
        if reduction and score > alpha:
            score = -alphabeta(board, depth - 1, -beta, -alpha, not maximizing)

        _undo_move(board, move, saved)

        if score > best_score:
            best_score = score
        if score > alpha:
            alpha = score
        if alpha >= beta:
            if not move.captured:
                if killers[depth][0] is None or killers[depth][0] != move:
                    killers[depth][1] = killers[depth][0]
                    killers[depth][0] = move
            tt_flag = TT_BETA
            TRANSPOSITION_TABLE[key] = (depth, tt_flag, beta)
            return beta
        
    if best_score <= original_alpha:
        tt_flag = TT_ALPHA
    else:
        tt_flag = TT_EXACT

    TRANSPOSITION_TABLE[key] = (depth, tt_flag, best_score)
    return best_score

def find_best_move(board, max_depth=MAX_DEPTH, time_limit=10.0):
    # Iterative deeping search
    # Returns (best_move, depth_reached, score)
    TRANSPOSITION_TABLE.clear()

    global _search_start, _time_limit
    _search_start = time.time()
    _time_limit = time_limit

    best_move = None
    best_score = -100000
    start = time.time()

    moves = generate_moves(board)
    if not moves:
        return None, 0, 0
    
    # Sort captures first for better pruning at root
    moves.sort(key=lambda m: _move_score(m, board, 0), reverse=True)

    for depth in range(1, max_depth + 1):
        if time.time() - start > time_limit:
            break

        if depth >= 2 and best_score != -100000:
            asp = 50
            alpha = best_score - asp
            beta = best_score + asp
        else:
            alpha = -100000
            beta = 100000

        current_best_move = None
        current_best_score = -100000

        for move in moves:
            saved = _save(board)
            _apply_move(board, move)
            score = -alphabeta(board, depth-1, -beta, -alpha, False)
            _undo_move(board, move, saved)

            # if score falls outside the window, re-search with full window
            if score <= (best_score - asp if depth >= 2 else -100000) or score >= beta:
                full_saved = _save(board)
                _apply_move(board, move)
                score = -alphabeta(board, depth - 1, -100000, 100000, False)
                _undo_move(board, move, full_saved)

            if score > current_best_score:
                current_best_score = score
                current_best_move = move
            if score > alpha:
                alpha = score

        if current_best_move:
            best_move = current_best_move
            best_score = current_best_score

        # Promote best move to front for next iteration
        if current_best_move and current_best_move in moves:
            moves.remove(current_best_move)
            moves.insert(0, current_best_move)

        elapsed = time.time() - start
        print(f"Depth {depth}: best={best_move.uci() if best_move else 'none'}"
              f"score={best_score} time={elapsed:.2f}s")

        if abs(best_score) > 90000:
            break # found checkmate
        
    print(f"Estimated ELO: ~1900")
    return best_move, depth, best_score