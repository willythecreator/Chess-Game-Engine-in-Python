import tkinter as tk
from board import Board
from PIL import Image, ImageTk

SQUARE_SIZE = 64

class ChessGUI:
    def __init__(self, root):
        self.root = root
        self.board = Board()
        self.canvas = tk.Canvas(root, width=8*SQUARE_SIZE, height=8*SQUARE_SIZE)
        self.canvas.pack()
        self.images = {}
        self._load_images()
        self.draw_board()
        self.draw_pieces()

    def _load_images(self):
        files = {'P': 'wP', 'N':'wN', 'B': 'wB', 'R':'wR', 'Q': 'wQ', 'K': 'wK',
                'p': 'bP', 'n': 'bN', 'b': 'bB', 'r': 'bR', 'q': 'bQ', 'k': 'bK'}
        for piece, name in files.items():
            img = Image.open(f'assets/pieces/{name}.png').resize((64, 64))
            self.images[piece] = ImageTk.PhotoImage(img)

    def draw_board(self):
        colors = ['#1a1a2e', '#16213e']
        for r in range(8):
            for f in range(8):
                x, y = f * SQUARE_SIZE, (7 - r) * SQUARE_SIZE
                self.canvas.create_rectangle(x, y, x+SQUARE_SIZE, y+SQUARE_SIZE,
                                            fill=colors[(r+f)%2], outline='')
                
    def draw_pieces(self):
        for piece, bb in self.board.bitboards.items():
            b = bb
            while b:
                sq = (b & -b).bit_length() - 1
                b &= b - 1
                f, r = sq % 8, sq // 8
                self.canvas.create_image(f*SQUARE_SIZE, (7-r)*SQUARE_SIZE,
                                        image=self.images[piece], anchor='nw')
                
if __name__ == '__main__':
    root = tk.Tk()
    root.title('Chess Game Engine')
    app = ChessGUI(root)
    root.mainloop()