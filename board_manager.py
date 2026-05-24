import pygame
import pygame.gfxdraw

from fen_loader import generate_board_from_fen
from constants import *
from loader import load_board
from piece import Piece

class BoardManager:
    def __init__(self):
        self.position = generate_board_from_fen(FEN)
        self.board_grid = load_board(BOARD_TYPE, SIZE, SIZE)
        self.chessboard = [[Piece() for _ in range(8)] for _ in range(8)]
        self.white_turn = True

        self.last_square = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
        self.new_square = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
        
        self.last_square_pos = pygame.Vector2(-TILE_SIZE, -TILE_SIZE)
        self.new_square_pos = pygame.Vector2(-TILE_SIZE, -TILE_SIZE)
        
        self.current_move = 0
        self.selected_piece = None
        
        self.mousex = 0
        self.mousey = 0
        
        self.valid_moves_overlay = pygame.Surface((SIZE, SIZE), pygame.SRCALPHA)
        
        self.load_position()
        pass

    def load_position(self):
        for i in range(len(self.position)):
            piece = self.position[i]

            x = START_X + (i % 8) * TILE_SIZE
            y = START_Y + (i // 8) * TILE_SIZE

            if piece == 'x':
                continue

            self.chessboard[i % 8][i // 8].init(piece, x, y)
        pass

    def draw_grid(self, screen):
        screen.blit(self.board_grid, (START_X, START_Y))

    def draw_pieces(self, screen):
        for i in range(8):
            for j in range(8):
                self.chessboard[i][j].show(screen)

    def update(self, mouse_pos):
        for i in range(8):
            for j in range(8):
                self.chessboard[i][j].update(mouse_pos)

    def draw(self, screen):
        self.draw_grid(screen)
        
        pygame.draw.rect(self.last_square, MOVE_COLOR, (0, 0, TILE_SIZE, TILE_SIZE))
        pygame.draw.rect(self.new_square, MOVE_COLOR, (0, 0, TILE_SIZE, TILE_SIZE))
        
        if self.selected_piece:
            for move in self.selected_piece.valid_moves:
                x = move[0] * TILE_SIZE + TILE_SIZE/2
                y = move[1] * TILE_SIZE + TILE_SIZE/2
                pygame.gfxdraw.filled_circle(self.valid_moves_overlay, int(x), int(y), int(TILE_SIZE//6), VALID_COLOR)
        else:
            self.valid_moves_overlay.fill(TRANSPARENT)
        
        screen.blit(self.last_square, self.last_square_pos)
        screen.blit(self.new_square, self.new_square_pos)
        screen.blit(self.valid_moves_overlay, (0, 0))
        
        self.draw_pieces(screen)
        
    def start_selecting(self):
        # Piece under the mouse
        current = self.chessboard[self.mousex][self.mousey]
        
        if self.selected_piece is None:
            if self.white_turn == current.white:
                current.select()
                current.calculate_valid_moves(self)
                self.selected_piece = current
                
    def move_piece(self):
        if self.selected_piece is not None:
            # Nothing on the square
            current = self.chessboard[self.mousex][self.mousey]
            if not current.initialized and self.selected_piece.piece_name is not None:
                self.last_square_pos = self.selected_piece.old_pos

                current.init(self.selected_piece.piece_name, self.mousex * TILE_SIZE, self.mousey * TILE_SIZE)
                self.new_square_pos = current.old_pos

                self.selected_piece.deinit()
                # Move complete
                self.white_turn = not self.white_turn
            else:
                # Own piece
                # Move incomplete
                if current.white == self.selected_piece.white:
                    self.selected_piece.unselect()

                # Capture
                else:
                    self.last_square_pos = self.selected_piece.old_pos

                    current.deinit()

                    current.init(self.selected_piece.piece_name, self.mousex * TILE_SIZE, self.mousey * TILE_SIZE)
                    self.new_square_pos = current.old_pos

                    self.selected_piece.deinit()

                    # Move complete
                    self.white_turn = not self.white_turn

            self.selected_piece = None