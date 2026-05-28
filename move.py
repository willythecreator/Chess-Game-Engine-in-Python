class Move:
    def __init__(self, from_sq, to_sq, piece, captured=None,
                promotion=None, en_passant=False, castling=False,
                double_push=False):
        self.from_sq = from_sq
        self.to_sq = to_sq
        self.piece = piece
        self.captured = captured
        self.promotion = promotion
        self.en_passant = en_passant
        self.castling = castling
        self.double_push = double_push

    def uci(self):
        files = 'abcdefgh'
        uci_str = f'{files[self.from_sq % 8]}{self.from_sq // 8 + 1}' \
                  f'{files[self.to_sq % 8]}{self.to_sq // 8 + 1}'
        if self.promotion:
            uci_str += self.promotion.lower()
        return uci_str
    
    def __repr__(self):
        return f'<Move {self.uci()}>'
    
    def __eq__(self, other):
        return (self.from_sq == other.from_sq and
                self.to_sq == other.to_sq and
                self.promotion == other.promotion)