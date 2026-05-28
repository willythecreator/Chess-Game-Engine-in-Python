SQUARES = {
    'a1': 0, 'b1': 1, 'c1': 2, 'd1': 3, 'e1': 4, 'f1': 5, 'g1': 6, 'h1': 7,
    'a2': 8, 'b2': 9, 'c2': 10, 'd2': 11, 'e2': 12, 'f2': 13, 'g2': 14, 'h2': 15,
    'a3': 16, 'b3': 17, 'c3': 18, 'd3': 19, 'e3': 20, 'f3': 21, 'g3': 22, 'h3': 23,
    'a4': 24, 'b4': 25, 'c4': 26, 'd4': 27, 'e4': 28, 'f4': 29, 'g4': 30, 'h4': 31,
    'a5': 32, 'b5': 33, 'c5': 34, 'd5': 35, 'e5': 36, 'f5': 37, 'g5': 38, 'h5': 39,
    'a6': 40, 'b6': 41, 'c6': 42, 'd6': 43, 'e6': 44, 'f6': 45, 'g6': 46, 'h6': 47,
    'a7': 48, 'b7': 49, 'c7': 50, 'd7': 51, 'e7': 52, 'f7': 53, 'g7': 54, 'h7': 55,
    'a8': 56, 'b8': 57, 'c8': 58, 'd8': 59, 'e8': 60, 'f8': 61, 'g8': 62, 'h8': 63,
}

def sa(file, rank):
    return rank * 8 + file

def rank_of(sq):
    return sq // 8

def file_of(sq):
    return sq % 8

def set_bit(bb, sq):
    return bb | (1 << sq)

def clear_bit(bb, sq):
    return bb & ~(1 << sq)

def get_bit(bb, sq):
    return (bb >> sq) & 1

def print_bitboard(bb):
    for r in range(7, -1, -1):
        row = ''
        for f in range(8):
            sq_idx = r * 8 + f
            row += '1 ' if (bb >> sq_idx) & 1 else '. '
        print(f'{r+1} {row}')
    print(' a b c d e f g h')

PIECE_SYMBOLS = {
    'P': '♙', 'N': '♘', 'B': '♗', 'R': '♖', 'Q': '♕', 'K': '♔',
    'p': '♟', 'n': '♞', 'b': '♝', 'r': '♜', 'q': '♛', 'k': '♚',
}

class Board:
    def __init__(self):
        self.bitboards = {
            'P': 0, 'N': 0, 'B': 0, 'R': 0, 'Q': 0, 'K': 0,
            'p': 0, 'n': 0, 'b': 0, 'r': 0, 'q': 0, 'k': 0,
        }
        self.side = 'w'
        self.castling = 0 # K Q k q bits
        self.ep = -1
        self.halfmove = 0
        self.fullmove = 1
        self._startpos()

    def _startpos(self):
        pieces = {
            'R': 'a1 h1', 'N': 'b1 g1', 'B': 'c1 f1', 'Q': 'd1', 'K': 'e1',
            'r': 'a8 h8', 'n': 'b8 g8', 'b': 'c8 f8', 'q': 'd8', 'k': 'e8',
        }
        for p, sqs in pieces.items():
            for s in sqs.split():
                self.bitboards[p] = set_bit(self.bitboards[p], SQUARES[s])
            for sq_name in 'a2 b2 c2 d2 e2 f2 g2 h2'.split():
                self.bitboards['P'] = set_bit(self.bitboards['P'], SQUARES[sq_name])
            for sq_name in 'a7 b7 c7 d7 e7 f7 g7 h7'.split():
                self.bitboards['p'] = set_bit(self.bitboards['p'], SQUARES[sq_name])
            self.castling = 0b1111

    def occupied(self, color):
        if color == 'w':
            return (self.bitboards['P'] | self.bitboards['N'] | 
                    self.bitboards['B'] | self.bitboards['R'] |
                    self.bitboards['Q'] | self.bitboards['K'])
        else:
            return (self.bitboards['p'] | self.bitboards['n'] | 
                    self.bitboards['b'] | self.bitboards['r'] |
                    self.bitboards['q'] | self.bitboards['k'])
        
    def all_occupied(self):
        return self.occupied('w') | self.occupied('b')
    
    def print_board(self):
        for r in range(7, -1, -1):
            row = f'{r+1} '
            for f in range(8):
                sq_idx = r * 8 + f
                found = False
                for piece_char, bb in self.bitboards.items():
                    if (bb >> sq_idx) & 1:
                        row += PIECE_SYMBOLS[piece_char] + ' '
                        found = True
                        break
                if not found:
                    row += '. '
            print(row)
        print(' a b c d e f g h')
        turn = "White" if self.side == 'w' else "Black"
        print(f'{turn} to move | Castling: {self.castling:04b} | Ep: {self.ep}')

if __name__ == '__main__':
    b = Board()
    b.print_board()