import tkinter as tk
from board import Board
from movegen import generate_moves, KING_ATTACKS, KNIGHT_ATTACKS, PAWN_ATTACKS, slider_attacks, DIRECTIONS
from move import Move
from PIL import Image, ImageTk, ImageDraw
import math
import os

SQ       = 80
BOARD_PX = SQ * 8
PANEL_H  = 88
NOTATE_W = 200
WIN_W    = NOTATE_W + BOARD_PX + NOTATE_W
WIN_H    = PANEL_H + BOARD_PX + PANEL_H

BG         = "#08090f"
LIGHT_SQ   = "#2e4a6e"
DARK_SQ    = "#162236"
HIGHLIGHT  = "#c8a84b"
HL_ALPHA   = 0.55
MOVE_DOT_C = "#7ab8f5"
MOVE_CAP_C = "#e05555"
ARROW_COL  = "#c8a84b"
CHECK_COL  = "#ff2222"
PANEL_BG   = "#0d1117"
NOTATE_BG  = "#0d1117"
ACCENT     = "#4a90d9"
ACCENT2    = "#c8a84b"
TEXT_MAIN  = "#dce8f5"
TEXT_SUB   = "#4a6080"
COORD_L    = "#7ab8f5"
COORD_D    = "#2e5a8a"
RANK_FILE  = "abcdefgh"
SEP_COL    = "#1a2a3a"


def blend(hex_color, alpha, bg_hex):
    def parse(h): return tuple(int(h.lstrip('#')[i:i+2], 16) for i in (0,2,4))
    fg, bg = parse(hex_color), parse(bg_hex)
    r = tuple(int(fg[i]*alpha + bg[i]*(1-alpha)) for i in range(3))
    return '#%02x%02x%02x' % r


class ChessGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Chilli Engine")
        self.root.configure(bg=BG)
        self.root.resizable(False, False)

        self.board      = Board()
        self.images     = {}
        self.piece_imgs = {}

        self.selected_sq = None
        self.legal_moves = []
        self.all_moves   = []

        self.arrow_start = None
        self.arrows      = []
        self.highlighted = set()

        self.drag_piece  = None
        self.drag_sq     = None
        self.drag_x      = 0
        self.drag_y      = 0
        self.drag_img_id = None
        self.is_dragging = False

        self.notation    = []
        self.in_check    = False
        self.king_sq     = None

        self.player_photo = None
        self._build_ui()
        self._load_images()
        self._load_chilli()
        self._load_player()
        self.all_moves = generate_moves(self.board)
        self._update_check()
        self.redraw()

    def _build_ui(self):
        self.top_panel = tk.Canvas(self.root, width=WIN_W, height=PANEL_H,
                                   bg=PANEL_BG, highlightthickness=0)
        self.top_panel.pack()

        mid = tk.Frame(self.root, bg=BG)
        mid.pack()

        self.left_panel = tk.Canvas(mid, width=NOTATE_W, height=BOARD_PX,
                                    bg=NOTATE_BG, highlightthickness=0)
        self.left_panel.pack(side=tk.LEFT)

        self.canvas = tk.Canvas(mid, width=BOARD_PX, height=BOARD_PX,
                                bg=BG, highlightthickness=0, cursor="hand2")
        self.canvas.pack(side=tk.LEFT)

        self.right_panel = tk.Canvas(mid, width=NOTATE_W, height=BOARD_PX,
                                     bg=NOTATE_BG, highlightthickness=0)
        self.right_panel.pack(side=tk.LEFT)

        self.bot_panel = tk.Canvas(self.root, width=WIN_W, height=PANEL_H,
                                   bg=PANEL_BG, highlightthickness=0)
        self.bot_panel.pack()

        tk.Frame(self.root, bg=SEP_COL, height=1).place(x=0, y=PANEL_H, width=WIN_W)
        tk.Frame(self.root, bg=SEP_COL, height=1).place(x=0, y=PANEL_H+BOARD_PX, width=WIN_W)

        self.canvas.bind("<Button-1>",        self._on_left_press)
        self.canvas.bind("<B1-Motion>",       self._on_drag_motion)
        self.canvas.bind("<ButtonRelease-1>", self._on_drag_release)
        self.canvas.bind("<Button-3>",        self._on_right_press)
        self.canvas.bind("<B3-Motion>",       self._on_right_drag)
        self.canvas.bind("<ButtonRelease-3>", self._on_right_release)

    def _load_images(self):
        mapping = {
            'P':'wP','N':'wN','B':'wB','R':'wR','Q':'wQ','K':'wK',
            'p':'bP','n':'bN','b':'bB','r':'bR','q':'bQ','k':'bK',
        }
        for piece, name in mapping.items():
            path = f'assets/pieces/{name}.png'
            img = Image.open(path).convert("RGBA").resize((SQ, SQ), Image.LANCZOS)
            self.piece_imgs[piece] = img
            self.images[piece]     = ImageTk.PhotoImage(img)

    def _load_chilli(self):
        self.chilli_photo = None
        AVATAR = 56
        candidates = [
            '/mnt/c/Coding/Game Chess Engine in Python/assets/1000_F_299092735_QX6RymeVU6mqysm1bVyFmKo9YtI3C89T.jpg',
            r'C:\Coding\Game Chess Engine in Python\assets\1000_F_299092735_QX6RymeVU6mqysm1bVyFmKo9YtI3C89T.jpg',
            'assets/chilli.jpg',
            'assets/chilli.png',
        ]
        for path in candidates:
            print(f"Trying: {path} -> exists: {os.path.exists(path)}")
            if os.path.exists(path):
                try:
                    img = Image.open(path).convert("RGBA")
                    w, h = img.size
                    side = min(w, h)
                    img  = img.crop(((w-side)//2, (h-side)//2,
                                     (w+side)//2, (h+side)//2))
                    img  = img.resize((AVATAR, AVATAR), Image.LANCZOS)
                    self.chilli_photo = ImageTk.PhotoImage(img)
                    print(f"Loaded successfully: {path}")
                    break
                except Exception as e:
                    print(f"Failed to load: {e}")

    def _load_player(self):
        self.player_photo = None
        AVATAR = 56
        candidates = [
            r'C:\Coding\Game Chess Engine in Python\assets\1000_F_299092735_QX6RymeVU6mqysm1bVyFmKo9YtI3C89T.jpg',
            'assets/player.jpg',
            'assets/player.png',
        ]
        for path in candidates:
            if os.path.exists(path):
                try:
                    img = Image.open(path).convert("RGBA")
                    w, h = img.size
                    side = min(w, h)
                    img = img.crop(((w-side)//2, (h-side)//2,
                                    (w+side)//2, (h+side)//2))
                    img = img.resize((AVATAR, AVATAR), Image.LANCZOS)
                    self.player_photo = ImageTk.PhotoImage(img)
                    break
                except Exception:
                    pass

    def _sq_to_xy(self, sq):
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

    def _update_check(self):
        side = self.board.side
        king_piece = 'K' if side == 'w' else 'k'
        bb = self.board.bitboards[king_piece]
        if bb == 0:
            self.in_check = False
            self.king_sq  = None
            return
        king_sq = (bb & -bb).bit_length() - 1
        self.king_sq = king_sq
        self.in_check = self._is_square_attacked(king_sq, side)

    def _is_square_attacked(self, sq, by_whom):
        # by_whom is the side whose king we're checking — attacker is the enemy
        enemy = 'b' if by_whom == 'w' else 'w'
        b     = self.board
        occ   = b.all_occupied()

        # Knight
        enemy_n = 'N' if enemy == 'w' else 'n'
        if KNIGHT_ATTACKS[sq] & b.bitboards[enemy_n]:
            return True

        # King
        enemy_k = 'K' if enemy == 'w' else 'k'
        if KING_ATTACKS[sq] & b.bitboards[enemy_k]:
            return True

        # Pawn
        enemy_p = 'P' if enemy == 'w' else 'p'
        if PAWN_ATTACKS[by_whom][sq] & b.bitboards[enemy_p]:
            return True

        # Rook / Queen (straight lines)
        enemy_r = 'R' if enemy == 'w' else 'r'
        enemy_q = 'Q' if enemy == 'w' else 'q'
        rook_attacks = slider_attacks(sq, occ, DIRECTIONS['rook'])
        if rook_attacks & (b.bitboards[enemy_r] | b.bitboards[enemy_q]):
            return True

        # Bishop / Queen (diagonals)
        enemy_b = 'B' if enemy == 'w' else 'b'
        bishop_attacks = slider_attacks(sq, occ, DIRECTIONS['bishop'])
        if bishop_attacks & (b.bitboards[enemy_b] | b.bitboards[enemy_q]):
            return True

        return False

    def redraw(self):
        self._draw_board()
        self._draw_notation()
        self._draw_player_cards()

    def _draw_board(self):
        self.canvas.delete("all")

        legal_cap = {m.to_sq for m in self.legal_moves if m.captured or m.en_passant}

        for sq in range(64):
            f, r  = sq % 8, sq // 8
            x, y  = self._sq_to_xy(sq)
            light = (f + r) % 2 == 0
            base  = LIGHT_SQ if light else DARK_SQ

            # King in check gets a red square
            if sq == self.king_sq and self.in_check:
                fill = blend(CHECK_COL, 0.6, base)
            elif sq == self.selected_sq:
                fill = blend(HIGHLIGHT, HL_ALPHA, base)
            elif sq in self.highlighted:
                fill = blend("#dd4444", 0.45, base)
            else:
                fill = base

            self.canvas.create_rectangle(x, y, x+SQ, y+SQ, fill=fill, outline="")

            coord_col = COORD_L if light else COORD_D
            if f == 0:
                self.canvas.create_text(x+4, y+4, text=str(r+1),
                    anchor="nw", fill=coord_col, font=("Courier", 10, "bold"))
            if r == 0:
                self.canvas.create_text(x+SQ-4, y+SQ-4, text=RANK_FILE[f],
                    anchor="se", fill=coord_col, font=("Courier", 10, "bold"))

        for m in self.legal_moves:
            tsq    = m.to_sq
            cx, cy = self._sq_centre(tsq)
            if tsq in legal_cap:
                r2 = SQ//2 - 4
                self.canvas.create_oval(cx-r2, cy-r2, cx+r2, cy+r2,
                    outline=MOVE_CAP_C, width=5, fill="")
            else:
                dot = SQ // 6
                self.canvas.create_oval(cx-dot, cy-dot, cx+dot, cy+dot,
                    fill=MOVE_DOT_C, outline="")

        for piece, bb in self.board.bitboards.items():
            b = bb
            while b:
                sq = (b & -b).bit_length() - 1
                b &= b - 1
                if sq == self.drag_sq and self.is_dragging:
                    continue
                x, y = self._sq_to_xy(sq)
                self.canvas.create_image(x, y, image=self.images[piece], anchor="nw")

        for (fsq, tsq) in self.arrows:
            self._draw_arrow(fsq, tsq, ARROW_COL)
        if self.arrow_start is not None and hasattr(self, '_arrow_cur'):
            self._draw_arrow(self.arrow_start, self._arrow_cur, "#aaccff")

        if self.drag_piece and self.is_dragging:
            offset = SQ // 2
            self.canvas.create_image(
                self.drag_x - offset, self.drag_y - offset,
                image=self.images[self.drag_piece], anchor="nw")

    def _draw_arrow(self, from_sq, to_sq, color):
        if from_sq == to_sq:
            return
        x1, y1 = self._sq_centre(from_sq)
        x2, y2 = self._sq_centre(to_sq)
        dx, dy  = x2-x1, y2-y1
        length  = math.hypot(dx, dy)
        if length == 0:
            return
        ux, uy = dx/length, dy/length
        W      = SQ // 7

        ex = x2 - ux * SQ * 0.38
        ey = y2 - uy * SQ * 0.38
        sx = x1 + ux * SQ * 0.32
        sy = y1 + uy * SQ * 0.32

        self.canvas.create_line(sx, sy, ex, ey,
            fill=color, width=W, capstyle=tk.BUTT, joinstyle=tk.MITER)

        px, py  = -uy, ux
        head_w  = SQ * 0.22
        tip = (x2, y2)
        bl  = (ex + px*head_w, ey + py*head_w)
        br  = (ex - px*head_w, ey - py*head_w)
        self.canvas.create_polygon(tip[0], tip[1], bl[0], bl[1], br[0], br[1],
            fill=color, outline="")

    def _draw_notation(self):
        self.left_panel.delete("all")
        self.right_panel.delete("all")

        self.left_panel.create_text(
            NOTATE_W//2, 22, text="MOVES",
            fill=ACCENT, font=("Courier", 11, "bold"), anchor="center")
        self.left_panel.create_line(12, 38, NOTATE_W-12, 38, fill=SEP_COL, width=1)

        y = 54
        for i in range(0, len(self.notation), 2):
            move_num = i // 2 + 1
            white    = self.notation[i]
            black    = self.notation[i+1] if i+1 < len(self.notation) else ""
            row      = f"{move_num:>2}. {white:<7} {black}"
            is_last  = (i >= len(self.notation) - 2)
            col      = TEXT_MAIN if is_last else TEXT_SUB
            self.left_panel.create_text(
                12, y, text=row, fill=col,
                font=("Courier", 10), anchor="nw")
            y += 18
            if y > BOARD_PX - 10:
                break

        self.right_panel.create_text(
            NOTATE_W//2, 22, text="ENGINE",
            fill=ACCENT, font=("Courier", 11, "bold"), anchor="center")
        self.right_panel.create_line(12, 38, NOTATE_W-12, 38, fill=SEP_COL, width=1)

        check_str = "CHECK!" if self.in_check else "—"
        check_col = CHECK_COL if self.in_check else TEXT_SUB

        infos = [
            ("Side",  "White" if self.board.side == 'w' else "Black", TEXT_MAIN),
            ("Move",  str(self.board.fullmove),                        TEXT_MAIN),
            ("Check", check_str,                                       check_col),
            ("EP sq", str(self.board.ep) if self.board.ep != -1 else "—", TEXT_SUB),
        ]
        y = 58
        for label, val, vcol in infos:
            self.right_panel.create_text(
                14, y, text=label, fill=TEXT_SUB,
                font=("Courier", 9, "bold"), anchor="nw")
            self.right_panel.create_text(
                NOTATE_W-14, y, text=val, fill=vcol,
                font=("Courier", 10), anchor="ne")
            y += 24

    def _draw_player_cards(self):
        self._draw_card(self.top_panel, "Chilli", "???",   is_chilli=True)
        self._draw_card(self.bot_panel, "You",    "Human", is_chilli=False)

    def _draw_card(self, panel, name, rating, is_chilli):
        panel.delete("all")
        w = WIN_W
        panel.create_rectangle(0, 0, w, PANEL_H, fill=PANEL_BG, outline="")

        AVATAR = 56
        PAD    = 16
        ax, ay = PAD, (PANEL_H - AVATAR) // 2

        if is_chilli and self.chilli_photo:
            panel.create_image(ax, ay, image=self.chilli_photo, anchor="nw")
            panel.create_rectangle(ax, ay, ax+AVATAR, ay+AVATAR,
                outline=ACCENT, width=1, fill="")
            
        else:
            col = "#12203a" if is_chilli else "#0a1628"
            char = name[0].upper() if is_chilli else "?"
            panel.create_rectangle(ax, ay, ax+AVATAR, ay+AVATAR,
                                   fill=col, outline=ACCENT2, width=1)
            panel.create_text(ax+AVATAR//2, ay+AVATAR//2, text=char,
                              fill=ACCENT2, font=("Courier", 22, "bold"), anchor="center")

        tx = ax + AVATAR + 14
        panel.create_text(tx, PANEL_H//2 - 12, text=name,
            fill=TEXT_MAIN, font=("Courier", 15, "bold"), anchor="w")
        panel.create_text(tx, PANEL_H//2 + 10, text=rating,
            fill=TEXT_SUB, font=("Courier", 10), anchor="w")

        side_text = "BLACK" if is_chilli else "WHITE"
        pill_fg   = "#cccccc" if is_chilli else "#111111"
        pill_bg   = "#1a1a1a" if is_chilli else "#eeeeee"
        px        = w - NOTATE_W - 20
        panel.create_rectangle(px-32, PANEL_H//2-11, px+32, PANEL_H//2+11,
            fill=pill_bg, outline="")
        panel.create_text(px, PANEL_H//2, text=side_text,
            fill=pill_fg, font=("Courier", 8, "bold"), anchor="center")

    def _on_left_press(self, event):
        sq = self._xy_to_sq(event.x, event.y)
        if sq is None:
            return

        if self.selected_sq is not None and not self.is_dragging:
            move = self._find_move(self.selected_sq, sq)
            if move:
                if move.promotion:
                    self._show_promotion_dialog(move)
                    return
                self._apply_move(move)
                self.selected_sq = None
                self.legal_moves = []
                self.arrows      = []
                self.highlighted = set()
                self.drag_piece  = None
                self.drag_sq     = None
                self.redraw()
                return

        piece_here = self._piece_at(sq)
        if piece_here and self._is_own(piece_here):
            self.selected_sq = sq
            self.drag_sq     = sq
            self.drag_piece  = piece_here
            self.drag_x      = event.x
            self.drag_y      = event.y
            self.legal_moves = [m for m in self.all_moves if m.from_sq == sq]
        else:
            self.selected_sq = None
            self.legal_moves = []
            self.drag_piece  = None
            self.drag_sq     = None
        self.redraw()

    def _on_drag_motion(self, event):
        if self.drag_piece is None:
            return
        self.is_dragging = True
        self.drag_x = event.x
        self.drag_y = event.y
        self._draw_board()

    def _on_drag_release(self, event):
        if self.drag_piece is None:
            return
        sq = self._xy_to_sq(event.x, event.y)

        if self.is_dragging and sq is not None and sq != self.drag_sq:
            move = self._find_move(self.drag_sq, sq)
            if move:
                if move.promotion:
                    self.drag_piece  = None
                    self.drag_sq     = None
                    self.is_dragging = False
                    self._show_promotion_dialog(move)
                    return
                self._apply_move(move)
                self.selected_sq = None
                self.legal_moves = []
                self.arrows      = []
                self.highlighted = set()

        self.drag_piece  = None
        self.drag_sq     = None
        self.is_dragging = False
        self.redraw()

    def _on_right_press(self, event):
        sq = self._xy_to_sq(event.x, event.y)
        self.arrow_start = sq
        self._arrow_cur  = sq

    def _on_right_drag(self, event):
        sq = self._xy_to_sq(event.x, event.y)
        if sq is not None and sq != self.arrow_start:
            self._arrow_cur = sq
            self._draw_board()

    def _on_right_release(self, event):
        sq = self._xy_to_sq(event.x, event.y)
        if sq is None:
            self.arrow_start = None
            return
        if sq == self.arrow_start:
            if sq in self.highlighted:
                self.highlighted.discard(sq)
            else:
                self.highlighted.add(sq)
        else:
            arrow = (self.arrow_start, sq)
            if arrow in self.arrows:
                self.arrows.remove(arrow)
            else:
                self.arrows.append(arrow)
        self.arrow_start = None
        if hasattr(self, '_arrow_cur'):
            del self._arrow_cur
        self.redraw()

    def _piece_at(self, sq):
        for piece, bb in self.board.bitboards.items():
            if (bb >> sq) & 1:
                return piece
        return None

    def _is_own(self, piece):
        return piece.isupper() if self.board.side == 'w' else piece.islower()

    def _find_move(self, from_sq, to_sq):
        for m in self.legal_moves:
            if m.from_sq == from_sq and m.to_sq == to_sq:
                return m
        return None

    def _show_promotion_dialog(self, base_move):
        side    = self.board.side
        choices = ['Q','R','B','N'] if side == 'w' else ['q','r','b','n']
        labels  = ['Queen','Rook','Bishop','Knight']
        CELL    = SQ + 10   # slightly bigger than piece so image fits
        PAD     = 16
        DLG_W   = CELL*4 + PAD*2 + 24
        DLG_H   = CELL + PAD*2 + 48

        dlg = tk.Toplevel(self.root)
        dlg.title("Promote pawn")
        dlg.configure(bg=PANEL_BG)
        dlg.resizable(False, False)
        dlg.grab_set()
        dlg.transient(self.root)
        self.root.update_idletasks()
        rx = self.root.winfo_rootx() + (WIN_W - DLG_W)//2
        ry = self.root.winfo_rooty() + (WIN_H - DLG_H)//2
        dlg.geometry(f"{DLG_W}x{DLG_H}+{rx}+{ry}")

        tk.Label(dlg, text="Choose promotion piece",
                 bg=PANEL_BG, fg=ACCENT2,
                 font=("Courier", 11, "bold")).pack(pady=(PAD, 8))

        frame  = tk.Frame(dlg, bg=PANEL_BG)
        frame.pack(padx=PAD)
        chosen = tk.StringVar(value="")

        def on_pick(p):
            chosen.set(p)
            dlg.destroy()

        for piece_char, label in zip(choices, labels):
            col = tk.Frame(frame, bg=PANEL_BG)
            col.pack(side=tk.LEFT, padx=6)

            c = tk.Canvas(col, width=CELL, height=CELL, bg="#12203a",
                          highlightthickness=2, highlightbackground=ACCENT,
                          cursor="hand2")
            c.pack()

            img = self.images.get(piece_char)
            if img:
                offset = (CELL - SQ) // 2
                c.create_image(CELL//2, CELL//2, image=img, anchor="center")

            c.bind("<Button-1>", lambda e, p=piece_char: on_pick(p))

            def _enter(e, cv=c): cv.config(highlightbackground=ACCENT2, bg="#1e3a5a")
            def _leave(e, cv=c): cv.config(highlightbackground=ACCENT,  bg="#12203a")
            c.bind("<Enter>", _enter)
            c.bind("<Leave>", _leave)

            tk.Label(col, text=label, bg=PANEL_BG, fg=TEXT_MAIN,
                     font=("Courier", 9)).pack(pady=(4,0))

        dlg.wait_window()
        picked = chosen.get()
        if not picked:
            self.selected_sq = None
            self.legal_moves = []
            self.redraw()
            return

        promo_move = None
        for m in self.legal_moves:
            if (m.from_sq == base_move.from_sq and m.to_sq == base_move.to_sq
                    and m.promotion and m.promotion.upper() == picked.upper()):
                promo_move = m
                break
        if promo_move is None:
            promo_move = base_move
            promo_move.promotion = picked

        self._apply_move(promo_move)
        self.selected_sq = None
        self.legal_moves = []
        self.arrows      = []
        self.highlighted = set()
        self.redraw()

    def _apply_move(self, move):
        b     = self.board
        piece = move.piece

        self.notation.append(move.uci())

        b.bitboards[piece] &= ~(1 << move.from_sq)

        if move.captured:
            b.bitboards[move.captured] &= ~(1 << move.to_sq)

        if move.castling:
            if move.to_sq == 6: # white kingside
                b.bitboards['R'] &= ~(1 << 7)
                b.bitboards['R'] |= (1 << 5)
                b.castling &= ~0b1100

            elif move.to_sq == 2: # white queenside
                b.bitboards['R'] &= ~(1 << 0)
                b.bitboards['R'] |= (1 << 3)
                b.castling &= ~0b1100

            elif move.to_sq == 62: # black kingside
                b.bitboards['r'] &= ~(1 << 63)
                b.bitboards['r'] |= (1 << 61)
                b.castling &= ~0b0011

            elif move.to_sq == 58: # black queenside
                b.bitboards['r'] &= ~(1 << 56)
                b.bitboards['r'] |= (1 << 59)
                b.castling &= ~0b0011
            

        if move.en_passant:
            ep_dir = -8 if b.side == 'w' else 8
            b.bitboards['p' if b.side == 'w' else 'P'] &= ~(1 << (move.to_sq + ep_dir))

        target_piece = move.promotion if move.promotion else piece
        b.bitboards[target_piece] |= 1 << move.to_sq

        b.ep   = move.to_sq + (-8 if b.side == 'w' else 8) if move.double_push else -1
        b.side = 'b' if b.side == 'w' else 'w'
        if b.side == 'w':
            b.fullmove += 1

        # Update castling rights
        if piece == 'K': b.castling &= ~0b1100
        if piece == 'k': b.castling &= ~0b0011
        if move.from_sq == 0: b.castling &= ~0b0100 # white queenside rook
        if move.from_sq == 7: b.castling &= ~0b1000 # white kingside rook 
        if move.from_sq == 56: b.castling &= ~0b0001 # black queenside rook
        if move.from_sq == 63: b.castling &= ~0b0010 # black kingside rook

        self.all_moves = generate_moves(self.board)
        self._update_check()

        # Check for checkmate or stalemate
        if len(self.all_moves) == 0:
            self.root.after(100, self._show_game_over)

    def _show_game_over(self):
        is_check = self.in_check
        title = "Checkmate" if is_check else "Stalemate"
        msg = ("Checkmate, game over bitch" if is_check
               else "Stalemate, draw bitch")
        
        dlg = tk.Toplevel(self.root)
        dlg.title(title)
        dlg.configure(bg=PANEL_BG)
        dlg.resizable(False, False)
        dlg.grab_set()
        dlg.transient(self.root)

        DLG_W, DLG_H = 320, 160
        self.root.update_idletasks()
        rx = self.root.winfo_rootx() + (WIN_W - DLG_W)//2
        ry = self.root.winfo_rooty() + (WIN_H - DLG_H)//2
        dlg.geometry(f"{DLG_W}x{DLG_H}+{rx}+{ry}")

        col=CHECK_COL if is_check else ACCENT
        tk.Label(dlg, text=title, bg=PANEL_BG, fg=col,
                 font=("Courier", 18, "bold")).pack(pady=(20, 4))
        tk.Label(dlg, text=msg, bg=PANEL_BG, fg=TEXT_SUB,
                 font=("Courier", 10)).pack(pady=(0, 16))
        
        btn_frame = tk.Frame(dlg, bg=PANEL_BG)
        btn_frame.pack()

        def restart():
            dlg.destroy()
            self._restart()

        def quit_game():
            self.root.destroy()

        tk.Button(btn_frame, text="Restart", bg=ACCENT, fg="#ffffff",
                  font=("Courier", 10, "bold"), relief="flat",
                  padx=16, pady=6, cursor="hand2", command=restart).pack(side=tk.LEFT, padx=8)
        
        tk.Button(btn_frame, text="Exit", bg="#2a1a1a", fg=TEXT_MAIN,
                  padx=16, pady=6, cursor="hand2",
                  command=quit_game).pack(side=tk.LEFT, padx=8)
        
    def _restart(self):
        self.board = Board()
        self.selected_sq = None
        self.legal_moves = []
        self.arrows = []
        self.highlighted = set()
        self.drag_piece = None
        self.drag_sq = None
        self.is_dragging = False
        self.notation = []
        self.in_check = False
        self.king_sq = None
        self.all_moves = generate_moves(self.board)
        self._update_check()
        self.redraw()

if __name__ == '__main__':
    root = tk.Tk()
    root.title("Chilli Engine")
    root.configure(bg=BG)

    app = ChessGUI(root)

    root.update_idletasks()
    sw = root.winfo_screenwidth()
    sh = root.winfo_screenheight()
    x  = (sw - WIN_W) // 2
    y  = (sh - WIN_H) // 2
    root.geometry(f"{WIN_W}x{WIN_H}+{x}+{y}")

    root.mainloop()