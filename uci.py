import sys
import threading
from board import Board
from search import find_best_move

def uci_loop():
    board = Board()

    while True:
        line = input().strip()
        if not line:
            continue

        if line == "uci":
            print("id name ChilliEngine")
            print("id author WIlly")
            print("option name Hash type spin default 64 min 1 max 512")
            print("uciok")

        elif line == "isready":
            print("readyok")

        elif line == "ucinewgame":
            board = Board()

        elif line.startswith("position"):
            board = parse_position(line)

        elif line.startswith("go"):
            move, depth, score = find_best_move(board)
            if move:
                print(f"bestmove {move.uci()}")
            else:
                print("bestmove 0000")

        elif line == "quit":
            sys.exit()

def parse_position(line):
    board = Board()
    tokens = line.split()
    idx = 1

    if tokens[idx] == "startpos":
        idx += 1
    elif tokens[idx] == "fen":
        # collect FEN string (6 parts)
        fen = " ".join(tokens[idx+1:idx+7])
        board = Board(fen)
        idx += 7

    if idx < len(tokens) and tokens[idx] == "moves":
        for uci_move in tokens[idx+1:]:
            apply_uci_move(board, uci_move)  

    return board

def apply_uci_move(board, uci_str):
    from movegen import generate_moves
    moves = generate_moves(board)
    for move in moves:
        if move.uci() == uci_str:
            from search import _apply_move
            _apply_move(board, move)
        return
    
if __name__ == "__main__":
    uci_loop()