import tkinter as tk
from tkinter import font as tkfont
from board import Board
from movegen import generate_moves
from move import Move
from PIL import Image, ImageTk, ImageDraw, ImageFilter
import math
import os

# Layout
SQ = 72 # square size in pixels
BOARD_PX = SQ * 8 # 576 (calculator btw)
SIDEBAR_W = 220 
PANEL_H = 100 # player card height (top & bottom)
WIN_W = BOARD_PX + SIDEBAR_W
WIN_H = BOARD_PX + PANEL_H * 2

# Palette
BG = "#0f0f13"
LIGHT_SQ = "#e8dcc8"
DARK_SQ = "#b08860"
HIGHLIGHT = "#f6f669" # selected square tint
HL_ALPHA = 0.45
MOVE_DOT = "#1a1a1a"
MOVE_CAP = "#cc3333"
ARROW_COL = "#f6a623"
ARROW_ALPHA = 0.82
PANEL_BG = "#1a1a22"
ACCENT = "#c9a96e"
TEXT_MAIN = "#f0ead8"
TEXT_SUB = "#7a7065"
COORD_DARK = "#d4bc98"
RANK_FILE = "abcdefgh"
COORD_LIGHT = "#8a6a40"

def blend(hex_color, alpha, bg_hex):
    def parse(h):
        return tuple(int(h.lstrip('#')[i:i+2], 16) for i in (0, 2, 4))
    fg, bg = parse(hex_color), parse(bg_hex)
    r = tuple(int(fg[i]*alpha + bg[i]*(1-alpha)) for i in range(3))
    return '#%02x%02x%02x' % r

class ChessGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Chess Game Engine")
        self.root.configure(bg=BG)
        self.root.resizable(False, False)

        self.board = Board()
        self.images = {}
        self.piece_imgs = {} # resized PIL images for composiitng
        self.selected_sq = None
        self.legal_moves = [] # move objects for selected piece
        self.all_moves = [] # all legal moves current side

        # arrow drawing state
        self.arrow_start = None # square where right-drag started
        self.arrows = [] # list of (from_sq, to_sq) to paint

        # Highlight squares (left-click marks)
        self.highlighted = set()

        # Drag variables
        self.drag_piece = None 
        self.drag_sq = None
        self.drag_x = 0
        self.drag_y = 0
        self.drag_img_id = None
        self.is_dragging = False

        self._build_ui()
        self._load_images()
        self._load_chilli()
        self.all_moves = generate_moves(self.board)
        self.redraw()

    # UI skeleton
    def _build_ui(self):
        # top player card (opponent - Chilli)
        self.top_panel =tk.Canvas(self.root, width=WIN_W, height=PANEL_H,
                                  bg = PANEL_BG, highlightthickness=0)
        self.top_panel.pack()

        # Middle row: board + sidebar
        mid = tk.Frame(self.root, bg=BG)
        mid.pack()

        self.canvas = tk.Canvas(
            mid, width=BOARD_PX, height=BOARD_PX,
            bg=BG, highlightthickness=0, cursor="hand2"
        )
        self.canvas.pack(side=tk.LEFT)

        self.sidebar = tk.Canvas(
            mid, width=SIDEBAR_W, height=BOARD_PX,
            bg=PANEL_BG, highlightthickness=0
        )
        self.sidebar.pack(side=tk.LEFT)

        # Bottom player card (yes, you)
        self.bot_panel = tk.Canvas(
            self.root, width=WIN_W, height=PANEL_H,
            bg=PANEL_BG, highlightthickness=0
        )
        self.bot_panel.pack()

        # Separator lines
        sep_cfg = dict(bg=ACCENT, height=1)
        tk.Frame(self.root, **sep_cfg).place(x=0, y=PANEL_H, width=WIN_W)
        tk.Frame(self.root, **sep_cfg).place(x=0, y=PANEL_H+BOARD_PX, width=WIN_W)

        # Board mouse bindings
        self.canvas.bind("<Button-1>", self._on_left_press)
        self.canvas.bind("<Button-3>", self._on_right_press)
        self.canvas.bind("<B3-Motion>", self._on_right_drag)
        self.canvas.bind("<ButtonRelease-3>", self._on_right_release)
        self.canvas.bind("<B1-Motion>", self._on_drag_motion)
        self.canvas.bind("<ButtonRelease-1>", self._on_drag_release)

    # Image loading
    def _load_images(self):
        mapping = {
            'P': 'wP', 'N': 'wN', 'B': 'wB', 
            'R': 'wR', 'Q': 'wQ', 'K': 'wK',
            'p': 'bP', 'n': 'bN', 'b': 'bB',
            'r': 'bR', 'q': 'bQ', 'k': 'bK',
        }
        for piece, name in mapping.items():
            path = f'assets/pieces/{name}.png'
            img = Image.open(path).convert("RGBA").resize((SQ, SQ), Image.LANCZOS)
            self.piece_imgs[piece] = img
            self.images[piece] = ImageTk.PhotoImage(img)
    
    def _load_chilli(self):
        # Load the photo, the retarted chihuahua
        self.chilli_photo = None
        candidates = [
            'assets/chilli.jpg',
            'assets/chilli.png',
            r'C:\Coding\Game Chess Engine in Python\assets\1000_F_299092735_QX6RymeVU6mqysm1bVyFmKo9YtI3C89T.jpg',
        ] 
        for path in candidates:
            if os.path.exists(path):
                try:
                    img = Image.open(path).convert("RGBA")

                    # Crop square from centre
                    w, h = img.size
                    side = min(w, h)
                    left = (w - side) // 2
                    top = (h - side) // 2
                    img = img.crop((left, top, left+side, top+side))
                    size = 64
                    img = img.resize((size, size),Image.LANCZOS)

                    # circle mask
                    mask = Image.new("L", (size, size), 0)
                    draw = ImageDraw.Draw(mask)
                    draw.ellipse((0, 0, size, size), fill=255)
                    img.putalpha(mask)
                    self.chilli_photo = ImageTk.PhotoImage(img)

                    break
                except Exception:
                    pass

    def _sq_to_xy(self, sq):
        # top left pixel of square (board canvas coords)
        f, r = sq % 8, sq // 8
        return f * SQ, (7 - r) * SQ
    
    def _xy_to_sq(self, x, y):
        f = x // SQ
        r = 7 - y // SQ
        if 0 <= f < 8 and 0 <= r < 8:
            return r * 8 + f
        return None
    
    def _sq_centre(self, sq):
        x, y = self._sq_to_xy(sq)
        return x + SQ//2, y + SQ//2
    
    # full redraw
    def redraw(self):
        self.canvas.delete("all")
        self._draw_sidebar()
        self._draw_player_cards()
        legal_to = {m.to_sq for m in self.legal_moves}
        legal_cap = {m.to_sq for m in self.legal_moves if m.captured or m.en_passant}
        for sq in range(64):
            f, r = sq % 8, sq // 8
            x, y = self._sq_to_xy(sq)
            light = (f + r) % 2 == 0
            base = LIGHT_SQ if light else DARK_SQ
            # Highlighted (right click mark or selected)
            if sq == self.selected_sq:
                fill = blend(HIGHLIGHT, HL_ALPHA, base)
            elif sq in self.highlighted:
                fill = blend("#ff4444", 0.40, base)
            else:
                fill = base
            self.canvas.create_rectangle(x, y, x+SQ, y+SQ, fill=fill, outline="")
            coord_col = COORD_DARK if light else COORD_LIGHT
            if f == 0: # rank numbers on left edge
                self.canvas.create_text(
                    x+4, y+4, text=str(r+1),
                    anchor="nw", fill=coord_col, font=("Georgia", 9, "bold")
                )
            if r == 0: # file letters on bottom edge
                self.canvas.create_text(
                    x+SQ-4, y+SQ-4, text=RANK_FILE[f],
                    anchor="se", fill=coord_col, font=("Georgia", 9, "bold")
                )
        # Legal move indicators
        for m in self.legal_moves:
            tsq = m.to_sq
            cx, cy = self._sq_centre(tsq)
            if tsq in legal_cap:
                # Ring around capture square
                r2 = SQ//2 -3
                self.canvas.create_oval(
                    cx-r2, cy-r2, cx+r2, cy+r2,
                    outline=MOVE_CAP, width=4, fill=""
                )
            else:
                # Small dot
                dot = SQ // 7
                self.canvas.create_oval(
                    cx-dot, cy-dot, cx+dot, cy+dot,
                    fill="#333333", outline=""
                )
        
        # Pieces
        for piece, bb in self.board.bitboards.items():
            b = bb
            while b:
                sq = (b & -b).bit_length() - 1
                b &= b - 1
                if sq == self.drag_sq:
                    continue
                x, y = self._sq_to_xy(sq)
                self.canvas.create_image(x, y, image=self.images[piece], anchor="nw")
        
        # Arrows
        for (fsq, tsq) in self.arrows:
            self._draw_arrow(fsq, tsq, ARROW_COL)
        # Arrow being drawn (live preview)
        if self.arrow_start is not None and hasattr(self, '_arrow_cur'):
            self._draw_arrow(self.arrow_start, self._arrow_cur, "#ffffff")

        # Floating piece while dragging
        if self.drag_piece and self.drag_x:
            offset = SQ // 2
            self.canvas.create_image(
                self.drag_x - offset,
                self.drag_y - offset,
                image=self.images[self.drag_piece],
                anchor="nw"
            )

    def _draw_arrow(self, from_sq, to_sq, color):
        if from_sq == to_sq:
            return
        x1, y1 = self._sq_centre(from_sq)
        x2, y2 = self._sq_centre(to_sq)
        dx, dy = x2 - x1, y2 - y1
        length = math.hypot(dx, dy)
        if length == 0:
            return
        ux , uy = dx/length, dy/length
        shaft_w = SQ // 6
        head_len = SQ // 2
        head_w = SQ // 3
        # Shorten to not overlap piece on destination
        ex = x2 - ux * (SQ * 0.35)
        ey = y2 - uy * (SQ * 0.35)
        # Shaft
        self.canvas.create_line(
            x1 + ux*SQ*0.3, y1 + uy*SQ*0.3,
            ex, ey,
            fill=color, width=shaft_w, capstyle=tk.ROUND, joinstyle=tk.ROUND
        )
        # Arrowhead (triangle)
        px, py = -uy, ux
        tip = (x2, y2)
        bl = (ex - ux*head_len + px*head_w, ey - uy*head_len + py*head_w)
        br = (ex - ux*head_len - px*head_w, ey - uy*head_len - py*head_w)
        self.canvas.create_polygon(
            tip[0], tip[1], bl[0], bl[1], br[0], br[1],
            fill=color, outline=""
        )
    # Sidebar
    def _draw_sidebar(self):
        self.sidebar.delete("all")
        w = SIDEBAR_W
        # Title
        self.sidebar.create_text(
            w//2, 30, text="CHILLI ENGINE", fill=ACCENT, font=("Georgia", 13, "bold"), anchor="center"
        )
        self.sidebar.create_line(16, 50, w-16, 50, fill=ACCENT, width=1)
        # Turn indicator
        turn_label = "White to move" if self.board.side == 'w' else "Black to move"
        dot_col = "#f0ead8" if self.board.side == 'w' else "#333333"
        dot_bg = "#f0ead8" if self.board.side == 'w' else "#444444"
        self.sidebar.create_oval(20, 68, 36, 84, fill=dot_bg, outline=ACCENT, width=1)
        self.sidebar.create_text(
            46, 76, text=turn_label, fill=TEXT_MAIN, font=("Georgia", 10), anchor="w"
        )
        # Move count
        self.sidebar.create_text(
            16, 108, text=f"Move {self.board.fullmove}",
            fill=TEXT_SUB, font=("Helvetica", 9), anchor="w"
        )
        # Instructions
        tips = [
            ("Left click", "select / move"),
            ("Right drag", "draw arrow"),
            ("Right click", "mark square"),
        ]
        self.sidebar.create_text(
            16, 150, text="CONTROLS",
            fill=ACCENT, font=("Helvetica", 8, "bold"), anchor="w"
        )
        for i, (key, val) in enumerate(tips):
            y = 170 + i * 32
            self.sidebar.create_text(
                16, y, text=key, fill=TEXT_SUB,
                font=("Helvetica", 9, "bold"), anchor="w"
            )
            self.sidebar.create_text(
                110, y, text=val, fill=TEXT_MAIN,
                font=("Helvetica", 9), anchor="w"
            )
    def _draw_player_cards(self):
        self._draw_card(self.top_panel, name="Chilli", rating="ELO: autistic", is_chilli=True)
        self._draw_card(self.bot_panel, name="You", rating="Human", is_chilli=False)

    def _draw_card(self, panel, name, rating, is_chilli):
        panel.delete("all")
        w = WIN_W
        # background stripe
        panel.create_rectangle(0, 0, w, PANEL_H, fill=PANEL_BG, outline="")
        # Avatar circle
        avatar_x, avatar_y, avatar_r = 40, PANEL_H//2, 30
        if is_chilli and self.chilli_photo:
            panel.create_image(avatar_x, avatar_y, image=self.chilli_photo, anchor="center")
        else:
            initial = name[0].upper()
            col = "#3a3020" if is_chilli else "#1e2a3a"
            panel.create_oval(
                avatar_x-avatar_r, avatar_y-avatar_r,
                avatar_x+avatar_r, avatar_y+avatar_r,
                fill=col, outline=ACCENT, width=1
            )
            panel.create_text(
                avatar_x, avatar_y, text=initial,
                fill=ACCENT, font=("Georgia", 18, "bold"), anchor="center"
            )
        
        # Name & rating
        panel.create_text(
            80, PANEL_H//2 - 12, text=name,
            fill=TEXT_MAIN, font=("Georgia", 14, "bold"), anchor="w"
        )
        panel.create_text(
            80, PANEL_H//2 + 12, text=rating,
            fill=TEXT_SUB, font=("Helvetica", 10), anchor="w"
        )
        # Side indicator pill
        side_text = "BLACK" if is_chilli else "WHITE"
        pill_col = "#222222" if is_chilli else "#eeeeee"
        text_col = "#cccccc" if is_chilli else "#111111"
        px = w - SIDEBAR_W - 80
        panel.create_rectangle(
            px-28, PANEL_H//2-12, px+28, PANEL_H//2+12,
            fill=pill_col, outline="", width=0
        )
        panel.create_text(
            px, PANEL_H//2, text=side_text,
            fill=text_col, font=("Helvetica", 8, "bold"), anchor="center"
        )
    def _on_left_press(self, event):
        sq = self._xy_to_sq(event.x, event.y)
        if sq is None:
            return
        # If we have a selected piece and this is a legal destination, then move
        if self.selected_sq is not None and not self.is_dragging:
            move = self._find_move(self.selected_sq, sq)
            if move:
                if move.promotion:
                    self._show_promotion_dialog(move)
                    return
                self._apply_move(move)
                self.selected_sq = None
                self.legal_moves = []
                self.arrows = []
                self.highlighted = set()
                self.drag_piece = None
                self.drag_sq = None
                self.redraw()
                return
            # No legal move found so fall through to reselect
            
        # Otherwise select the clicked piece (if it belongs to current side)
        piece_here = self._piece_at(sq)
        if piece_here and self._is_own(piece_here):
            self.selected_sq = sq
            self.drag_sq = sq
            self.drag_piece = piece_here
            self.drag_x = event.x
            self.drag_y = event.y
            self.legal_moves = [m for m in self.all_moves if m.from_sq == sq]
        else:
            self.selected_sq = None
            self.legal_moves = []
            self.drag_piece = None
            self.drag_sq = None
        self.redraw()
    def _on_right_press(self, event):
        sq = self._xy_to_sq(event.x, event.y)
        self.arrow_start = sq
        self._arrow_cur = sq

    def _on_right_drag(self, event):
        sq = self._xy_to_sq(event.x, event.y)
        if sq is not None and sq != self.arrow_start:
            self._arrow_cur = sq
            self.redraw()

    def _on_right_release(self, event):
        sq = self._xy_to_sq(event.x, event.y)
        if sq is None:
            self.arrow_start = None
            return
        
        if sq == self.arrow_start:
            # Toggle square highlight
            if sq in self.highlighted:
                self.highlighted.discard(sq)
            else:
                self.highlighted.add(sq)

        else:
            # Toggle arrow
            arrow = (self.arrow_start, sq)
            if arrow in self.arrows:
                self.arrows.remove(arrow)
            else:
                self.arrows.append(arrow)

        self.arrow_start = None
        if hasattr(self, '_arrow_cur'):
            del self._arrow_cur
        self.redraw()

    def _on_drag_motion(self, event):
        if self.drag_piece is None:
            return
        self.is_dragging = True
        self.drag_x = event.x
        self.drag_y = event.y
        self.redraw() # redraws board plus floating pieces

    def _on_drag_release(self, event):
        if self.drag_piece is None:
            return
        sq = self._xy_to_sq(event.x, event.y)

        # Only treats as a drag move if released on a different square
        if self.is_dragging and sq is not None and sq != self.drag_sq:
            move = self._find_move(self.drag_sq, sq)
            if move:
                if move.promotion:
                    self.drag_piece = None
                    self.drag_sq = None
                    self.is_dragging = False
                    self._show_promotion_dialog(move)
                    return
                self._apply_move(move)
                self.selected_sq = None
                self.legal_moves = []
                self.arrows = []
                self.highlighted = set()

        # If released on same square it was a click not a drag
        # Just clear drag state but keep selection alive for a click-to-move
        self.drag_piece = None
        self.drag_sq = None
        self.is_dragging = False
        self.redraw()

    # Move helpers
    def _piece_at(self, sq):
        for piece, bb in self.board.bitboards.items():
            if (bb >> sq) & 1:
                return piece
        return None
        
    def _is_own(self, piece):
        return piece.isupper() if self.board.side == 'w' else piece.islower()
    
    def _find_move(self, from_sq, to_sq):
        # Return the first signal move from/to (promotion picks are handled separately)
        for m in self.legal_moves:
            if m.from_sq == from_sq and m.to_sq == to_sq:
                return m
        return None
    
    def _show_promotion_dialog(self, base_move):
        side = self.board.side
        choices = ['Q', 'R', 'B', 'N'] if side == 'w' else ['q', 'r', 'b', 'n']
        labels = ['Queen', 'Rook', 'Bishop', 'Knight']
        CELL = 90
        PAD = 16
        DLG_W = CELL * 4 + PAD * 2
        DLG_H = CELL + PAD * 2 + 40
        dlg = tk.Toplevel(self.root)
        dlg.title("Promote pawn")
        dlg.configure(bg=PANEL_BG)
        dlg.resizable(False, False)
        dlg.grab_set()
        dlg.transient(self.root)
        self.root.update_idletasks()
        rx = self.root.winfo_rootx() + (WIN_W - DLG_W) // 2
        ry = self.root.winfo_rooty() + (WIN_H - DLG_H) // 2
        dlg.geometry(f"{DLG_W}x{DLG_H}+{rx}+{ry}")
        tk.Label(dlg, text="Choose promotion piece",
                 bg=PANEL_BG, fg=ACCENT,
                 font=("Georgia", 11, "bold")).pack(pady=(PAD, 6))
        
        frame = tk.Frame(dlg, bg=PANEL_BG)
        frame.pack()
        chosen = tk.StringVar(value="")

        def on_pick(piece_char):
            chosen.set(piece_char)
            dlg.destroy()

        for piece_char, label in zip(choices, labels):
            col = tk.Frame(frame, bg=PANEL_BG)
            col.pack(side=tk.LEFT, padx=6)
            c = tk.Canvas(col, width=CELL, height=CELL,  highlightthickness=1, highlightbackground=ACCENT, cursor="hand2")
            c.pack()
            img = self.images.get(piece_char)
            if img:
                offset = (CELL - SQ) // 2
                c.create_image(offset, offset, image=img, anchor="nw")
            c.bind("<Button-1>", lambda e, p=piece_char: on_pick(p))
            def _enter(e, cv=c): cv.config(highlightbackground="#ffffff", bg="#3a3a50")
            def _leave(e, cv=c): cv.config(highlightbackground=ACCENT, bg="#2a2a35")
            c.bind("<Enter>", _enter)
            c.bind("<Leave>", _leave)
            tk.Label(col, text=label, bg=PANEL_BG, fg=TEXT_MAIN, font=("Helvetica", 9)).pack(pady=(4, 0))
        
        dlg.wait_window()
        picked = chosen.get()
        if not picked:
            self.selected_sq = None
            self.legal_moves = []
            self.redraw()
            return
        
        promo_move = None
        for m in self.legal_moves:
            if m.from_sq == base_move.from_sq and m.to_sq == base_move.to_sq  and m.promotion and m.promotion.upper() == picked.upper():
                promo_move = m
                break

        if promo_move is None:
            promo_move = base_move
            promo_move.promotion = picked
        self._apply_move(promo_move)
        self.selected_sq = None
        self.legal_moves = []
        self.arrows = []
        self.highlighted = set()
        self.redraw()
    
    def _apply_move(self, move):
        # Apply move to boar (basic - promotion defaults to queen)
        b = self.board
        piece = move.piece
        # Remove from source
        b.bitboards[piece] &= ~(1 << move.from_sq)
        # Remove captured piece
        if move.captured:
            b.bitboards[move.captured] &= ~(1 << move.to_sq)
        # En passant captured
        if move.en_passant:
            ep_dir = -8 if b.side == 'w' else 8
            b.bitboards['p' if b.side == 'w' else 'P'] &= ~(1 << (move.to_sq + ep_dir))
        # Place piece (promotion to queen)
        target_piece = move.promotion if move.promotion else piece
        b.bitboards[target_piece] |= 1 << move.to_sq
        # Update en passant square
        b.ep = move.to_sq + (-8 if b.side == 'w' else 8) if move.double_push else - 1
        # Flip side
        b.side = 'b' if b.side == 'w' else 'w'
        if b.side == 'w':
            b.fullmove += 1
            # Regenerate moves
        self.all_moves = generate_moves(self.board)

# Entry point
if __name__ == '__main__':
    root = tk.Tk()
    root.title("Chess Game ENgine - Chilli")
    root.configure(bg=BG)

    app = ChessGUI(root)

    # Centre window on screen
    root.update_idletasks()
    sw = root.winfo_screenwidth()
    sh = root.winfo_screenheight()
    x = (sw - WIN_W) // 2
    y = (sh - WIN_H) // 2
    root.geometry(f"{WIN_W}x{WIN_H}+{x}+{y}")

    root.mainloop()