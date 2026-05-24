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
        self.draw_pieces(screen)