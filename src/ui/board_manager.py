import pygame
import pygame.gfxdraw
import chess
import math

from src.constants import *
from src.ui.loader import theme_manager

class BoardManager:
    def __init__(self):
        # Colors (Chess.com style - RGBA)
        self.COLOR_BEST = (34, 177, 76, 180)    # Green
        self.COLOR_THREAT = (237, 28, 36, 180)  # Red
        self.COLOR_USER = (255, 201, 14, 180)   # Yellow/Orange
        self.COLOR_CHECK = (255, 0, 0, 150)     # Bright Red for check
        
        # --- Settings (Controlled by UI) ---
        self.show_best_move = True
        self.show_threats = False
        self.show_annotations = True
        self.enable_animations = True
        self.flipped = False 
        
        self.reset()

    def reset(self, start_fen=FEN):
        self.start_fen = start_fen
        self.master_board = chess.Board(self.start_fen)
        self.view_ply = 0
        self.board = self.master_board.copy()
        
        self.last_square = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
        self.new_square = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
        self.last_square_pos = pygame.Vector2(-TILE_SIZE, -TILE_SIZE)
        self.new_square_pos = pygame.Vector2(-TILE_SIZE, -TILE_SIZE)
        
        self.selected_square = None
        self.valid_moves = []
        self.mousex = 0
        self.mousey = 0
        self.valid_moves_overlay = pygame.Surface((SIZE, SIZE), pygame.SRCALPHA)
        
        self.arrows = []
        self.circles = []
        self.right_click_start = None
        self.best_move_suggestion = None
        self.threat_moves = []

        # --- Transition Animation State ---
        self.active_animations = [] # List of { 'img': str, 'start': Vec2, 'end': Vec2 }
        self.animation_duration = 0.15 # Fast and snappy
        self.animation_timer = 1.0 # Start in finished state

    @property
    def white_turn(self):
        return self.board.turn == chess.WHITE

    def sq_to_screen(self, square):
        f, r = chess.square_file(square), chess.square_rank(square)
        if self.flipped: return 7 - f, r
        else: return f, 7 - r

    def screen_to_sq(self, gx, gy):
        if self.flipped: return chess.square(7 - gx, gy)
        else: return chess.square(gx, 7 - gy)

    def _get_offboard_pos(self, square):
        """Calculates a position outside the board nearest to the given square."""
        file, rank = self.sq_to_screen(square)
        # Determine nearest edge
        dist_left = file
        dist_right = 7 - file
        dist_top = rank
        dist_bottom = 7 - rank
        
        m = min(dist_left, dist_right, dist_top, dist_bottom)
        if m == dist_left: return pygame.Vector2(-TILE_SIZE, rank * TILE_SIZE)
        if m == dist_right: return pygame.Vector2(SIZE + TILE_SIZE, rank * TILE_SIZE)
        if m == dist_top: return pygame.Vector2(file * TILE_SIZE, -TILE_SIZE)
        return pygame.Vector2(file * TILE_SIZE, SIZE + TILE_SIZE)

    def plan_transition(self, board_from, board_to):
        """Computes move paths for all pieces to reconcile two board states."""
        if not self.enable_animations:
            self.animation_timer = 1.0
            return

        self.active_animations = []
        map_from = board_from.piece_map()
        map_to = board_to.piece_map()
        
        from_groups = {}
        for sq, p in map_from.items():
            from_groups.setdefault((p.color, p.piece_type), []).append(sq)
            
        to_groups = {}
        for sq, p in map_to.items():
            to_groups.setdefault((p.color, p.piece_type), []).append(sq)
            
        all_ids = set(from_groups.keys()) | set(to_groups.keys())
        
        for p_id in all_ids:
            sqs_from = from_groups.get(p_id, [])
            sqs_to = to_groups.get(p_id, [])
            
            # Match existing pieces by proximity (Greedy)
            while sqs_from and sqs_to:
                best_pair = None; min_dist = 999999
                for f in sqs_from:
                    for t in sqs_to:
                        # Use grid distance for matching
                        d = (f % 8 - t % 8)**2 + (f // 8 - t // 8)**2
                        if d < min_dist:
                            min_dist = d; best_pair = (f, t)
                
                f, t = best_pair
                p_name = ('w' if p_id[0] == chess.WHITE else 'b') + chess.piece_symbol(p_id[1])
                f_gx, f_gy = self.sq_to_screen(f)
                t_gx, t_gy = self.sq_to_screen(t)
                
                self.active_animations.append({
                    'img': p_name,
                    'start': pygame.Vector2(f_gx * TILE_SIZE, f_gy * TILE_SIZE),
                    'end': pygame.Vector2(t_gx * TILE_SIZE, t_gy * TILE_SIZE)
                })
                sqs_from.remove(f); sqs_to.remove(t)
            
            # Leftover pieces in FROM -> Fly off to graveyard
            p_name = ('w' if p_id[0] == chess.WHITE else 'b') + chess.piece_symbol(p_id[1])
            for f in sqs_from:
                gx, gy = self.sq_to_screen(f)
                self.active_animations.append({
                    'img': p_name,
                    'start': pygame.Vector2(gx * TILE_SIZE, gy * TILE_SIZE),
                    'end': self._get_offboard_pos(f)
                })
            
            # Leftover pieces in TO -> Fly in from outside
            for t in sqs_to:
                gx, gy = self.sq_to_screen(t)
                self.active_animations.append({
                    'img': p_name,
                    'start': self._get_offboard_pos(t),
                    'end': pygame.Vector2(gx * TILE_SIZE, gy * TILE_SIZE)
                })

        self.animation_timer = 0.0

    def set_view_ply(self, ply, animate=True):
        """Update the displayed board to a historical position with transition logic."""
        old_board = self.board.copy()
        self.view_ply = max(0, min(ply, len(self.master_board.move_stack)))
        
        self.board = chess.Board(self.start_fen)
        for move in self.master_board.move_stack[:self.view_ply]:
            self.board.push(move)
        
        if animate: self.plan_transition(old_board, self.board)
        
        if len(self.board.move_stack) > 0:
            last_move = self.board.move_stack[-1]
            f_file, f_rank = self.sq_to_screen(last_move.from_square)
            t_file, t_rank = self.sq_to_screen(last_move.to_square)
            self.last_square_pos = pygame.Vector2(f_file * TILE_SIZE, f_rank * TILE_SIZE)
            self.new_square_pos = pygame.Vector2(t_file * TILE_SIZE, t_rank * TILE_SIZE)
        else:
            self.last_square_pos = pygame.Vector2(-TILE_SIZE, -TILE_SIZE)
            self.new_square_pos = pygame.Vector2(-TILE_SIZE, -TILE_SIZE)
            
        self.selected_square, self.valid_moves, self.arrows, self.circles, self.best_move_suggestion = None, [], [], [], None

    def draw_grid(self, screen):
        if self.flipped:
            flipped_bg = pygame.transform.flip(theme_manager.board_image, True, True)
            screen.blit(flipped_bg, (START_X, START_Y))
        else:
            screen.blit(theme_manager.board_image, (START_X, START_Y))

    def draw_coordinates(self, screen):
        font = pygame.font.SysFont('Arial', 14, bold=True)
        files = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h']
        ranks = ['1', '2', '3', '4', '5', '6', '7', '8']
        if self.flipped: files.reverse()
        else: ranks.reverse()
        for i in range(8):
            rank_text = ranks[i]
            is_dark_sq = (i % 2 != 0) if not self.flipped else (i % 2 == 0)
            color = (255, 255, 255) if is_dark_sq else (0, 0, 0)
            lbl = font.render(rank_text, True, color)
            screen.blit(lbl, (START_X + 5, START_Y + i * TILE_SIZE + 5))
            file_text = files[i]
            is_dark_sq = (i % 2 == 0) if not self.flipped else (i % 2 != 0)
            color = (255, 255, 255) if is_dark_sq else (0, 0, 0)
            lbl = font.render(file_text, True, color)
            screen.blit(lbl, (START_X + (i+1) * TILE_SIZE - 15, START_Y + SIZE - 20))

    def draw_pieces(self, screen):
        # If we are currently animating a board transition, draw only the animated pieces
        if self.enable_animations and self.animation_timer < self.animation_duration:
            t = self.animation_timer / self.animation_duration
            t = 1 - (1 - t) * (1 - t) # Ease out quad
            
            for anim in self.active_animations:
                pos = anim['start'].lerp(anim['end'], t)
                img = theme_manager.piece_images[anim['img']]
                screen.blit(img, pos)
            return

        # Regular rendering
        piece_map = self.board.piece_map()
        for square, piece in piece_map.items():
            if square == self.selected_square and pygame.mouse.get_pressed()[0]:
                continue
            file, rank = self.sq_to_screen(square)
            img_name = ('w' if piece.color == chess.WHITE else 'b') + piece.symbol().lower()
            img = theme_manager.piece_images[img_name]
            screen.blit(img, (file * TILE_SIZE, rank * TILE_SIZE))

    def update(self, mouse_pos, dt):
        self.mousex = mouse_pos[0] // TILE_SIZE
        self.mousey = mouse_pos[1] // TILE_SIZE
        
        if self.animation_timer < self.animation_duration:
            self.animation_timer += dt
            if self.animation_timer >= self.animation_duration:
                self.active_animations = []

    def draw_arrow(self, screen, start_sq, end_sq, color):
        f1, r1 = self.sq_to_screen(start_sq); f2, r2 = self.sq_to_screen(end_sq)
        sp = pygame.Vector2(f1 * TILE_SIZE + TILE_SIZE/2, r1 * TILE_SIZE + TILE_SIZE/2)
        ep = pygame.Vector2(f2 * TILE_SIZE + TILE_SIZE/2, r2 * TILE_SIZE + TILE_SIZE/2)
        if sp == ep: return
        thickness, head_size = 18, 36
        temp_surf = pygame.Surface((SIZE, SIZE), pygame.SRCALPHA)
        dx, dy = abs(f2 - f1), abs(r2 - r1)
        if (dx == 1 and dy == 2) or (dx == 2 and dy == 1):
            if dx > dy: elbow = pygame.Vector2(f2 * TILE_SIZE + TILE_SIZE/2, r1 * TILE_SIZE + TILE_SIZE/2)
            else: elbow = pygame.Vector2(f1 * TILE_SIZE + TILE_SIZE/2, r2 * TILE_SIZE + TILE_SIZE/2)
            pygame.draw.circle(temp_surf, color, (int(sp.x), int(sp.y)), thickness // 2)
            pygame.draw.line(temp_surf, color, sp, elbow, thickness)
            pygame.draw.circle(temp_surf, color, (int(elbow.x), int(elbow.y)), thickness // 2)
            direction = (ep - elbow).normalize(); line_end = ep - direction * (head_size * 0.7)
            pygame.draw.line(temp_surf, color, elbow, line_end, thickness)
            pygame.draw.circle(temp_surf, color, (int(line_end.x), int(line_end.y)), thickness // 2); angle = math.atan2(direction.y, direction.x)
        else:
            direction = (ep - sp).normalize(); line_end = ep - direction * (head_size * 0.7)
            pygame.draw.circle(temp_surf, color, (int(sp.x), int(sp.y)), thickness // 2)
            pygame.draw.line(temp_surf, color, sp, line_end, thickness)
            pygame.draw.circle(temp_surf, color, (int(line_end.x), int(line_end.y)), thickness // 2); angle = math.atan2(direction.y, direction.x)
        p1 = ep + pygame.Vector2(head_size, 0).rotate(math.degrees(angle) + 150)
        p2 = ep + pygame.Vector2(head_size, 0).rotate(math.degrees(angle) - 150)
        pygame.draw.polygon(temp_surf, color, [ep, p1, p2]); screen.blit(temp_surf, (0, 0))

    def draw(self, screen, mouse_pos):
        self.draw_grid(screen); self.draw_coordinates(screen)
        pygame.draw.rect(self.last_square, MOVE_COLOR, (0, 0, TILE_SIZE, TILE_SIZE))
        pygame.draw.rect(self.new_square, MOVE_COLOR, (0, 0, TILE_SIZE, TILE_SIZE))
        screen.blit(self.last_square, self.last_square_pos); screen.blit(self.new_square, self.new_square_pos)
        if self.board.is_check():
            ks = self.board.king(self.board.turn); kf, kr = self.sq_to_screen(ks)
            cs = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA); pygame.draw.rect(cs, self.COLOR_CHECK, (0, 0, TILE_SIZE, TILE_SIZE)); screen.blit(cs, (kf * TILE_SIZE, kr * TILE_SIZE))
        self.valid_moves_overlay.fill(TRANSPARENT)
        if self.selected_square is not None:
            for move in self.valid_moves:
                dest = move.to_square; file, rank = self.sq_to_screen(dest); center = (int(file * TILE_SIZE + TILE_SIZE/2), int(rank * TILE_SIZE + TILE_SIZE/2))
                if not self.board.piece_at(dest): pygame.gfxdraw.filled_circle(self.valid_moves_overlay, center[0], center[1], int(TILE_SIZE//6), VALID_EMPTY_COLOR)
                else: pygame.draw.circle(self.valid_moves_overlay, VALID_ATTACK_COLOR, center, TILE_SIZE // 2, 8)
        screen.blit(self.valid_moves_overlay, (0, 0)); self.draw_pieces(screen)
        if self.selected_square is not None and pygame.mouse.get_pressed()[0]:
            piece = self.board.piece_at(self.selected_square)
            if piece:
                img_n = ('w' if piece.color == chess.WHITE else 'b') + piece.symbol().lower(); img = theme_manager.piece_images[img_n]
                screen.blit(img, (mouse_pos[0] - TILE_SIZE/2, mouse_pos[1] - TILE_SIZE/2))
        temp_annot_surf = pygame.Surface((SIZE, SIZE), pygame.SRCALPHA)
        if self.show_annotations:
            for sq, color in self.circles:
                f, r = self.sq_to_screen(sq); pygame.draw.circle(temp_annot_surf, color, (f * TILE_SIZE + TILE_SIZE/2, r * TILE_SIZE + TILE_SIZE/2), TILE_SIZE//2 - 2, 8)
            screen.blit(temp_annot_surf, (0,0))
            for start, end, color in self.arrows: self.draw_arrow(screen, start, end, color)
        if self.show_best_move and self.best_move_suggestion: self.draw_arrow(screen, self.best_move_suggestion.from_square, self.best_move_suggestion.to_square, self.COLOR_BEST)
        if self.show_threats:
            for move in self.threat_moves: self.draw_arrow(screen, move.from_square, move.to_square, self.COLOR_THREAT)

    def handle_click(self, pos, button):
        grid_x, grid_y = pos[0] // TILE_SIZE, pos[1] // TILE_SIZE
        if not (0 <= grid_x < 8 and 0 <= grid_y < 8): return
        square = self.screen_to_sq(grid_x, grid_y)
        if button == 1:
            self.arrows, self.circles = [], []
            if self.selected_square is None:
                piece = self.board.piece_at(square)
                if piece and piece.color == self.board.turn:
                    self.selected_square = square; self.valid_moves = [m for m in self.board.legal_moves if m.from_square == square]
            else:
                move = self._get_move(self.selected_square, square)
                if move in self.valid_moves: self._execute_move(move, animate=True); self.selected_square, self.valid_moves = None, []
                else:
                    piece = self.board.piece_at(square)
                    if piece and piece.color == self.board.turn:
                        self.selected_square = square; self.valid_moves = [m for m in self.board.legal_moves if m.from_square == square]
                    else: self.selected_square, self.valid_moves = None, []
        elif button == 3: self.right_click_start = square

    def handle_release(self, pos, button):
        grid_x, grid_y = pos[0] // TILE_SIZE, pos[1] // TILE_SIZE
        if not (0 <= grid_x < 8 and 0 <= grid_y < 8): return
        square = self.screen_to_sq(grid_x, grid_y)
        if button == 1:
            if self.selected_square is not None and self.selected_square != square:
                move = self._get_move(self.selected_square, square)
                if move in self.valid_moves: self._execute_move(move, animate=False); self.selected_square, self.valid_moves = None, []
        elif button == 3:
            if self.right_click_start == square:
                existing = [c for c in self.circles if c[0] == square]
                if existing: self.circles.remove(existing[0])
                else: self.circles.append((square, self.COLOR_USER))
            elif self.right_click_start is not None:
                existing = [a for a in self.arrows if a[0] == self.right_click_start and a[1] == square]
                if existing: self.arrows.remove(existing[0])
                else: self.arrows.append((self.right_click_start, square, self.COLOR_USER))
            self.right_click_start = None

    def _get_move(self, from_sq, to_sq):
        piece = self.board.piece_at(from_sq); promotion = None
        if piece and piece.piece_type == chess.PAWN:
            if (piece.color == chess.WHITE and chess.square_rank(to_sq) == 7) or (piece.color == chess.BLACK and chess.square_rank(to_sq) == 0): promotion = chess.QUEEN
        return chess.Move(from_sq, to_sq, promotion=promotion)

    def _execute_move(self, move, animate=True):
        old_board = self.board.copy()
        if self.view_ply < len(self.master_board.move_stack):
            while len(self.master_board.move_stack) > self.view_ply: self.master_board.pop()
        self.master_board.push(move)
        self.board = self.master_board.copy()
        self.view_ply = len(self.master_board.move_stack)
        
        if animate: self.plan_transition(old_board, self.board)
        
        last_move = self.board.move_stack[-1]; f_file, f_rank = self.sq_to_screen(last_move.from_square); t_file, t_rank = self.sq_to_screen(last_move.to_square)
        self.last_square_pos = pygame.Vector2(f_file * TILE_SIZE, f_rank * TILE_SIZE); self.new_square_pos = pygame.Vector2(t_file * TILE_SIZE, t_rank * TILE_SIZE)
        self.best_move_suggestion, self.threat_moves, self.arrows, self.circles = None, [], [], []
