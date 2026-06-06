import pygame
from src.constants import *


def load_board(board_type, width, height):
    try:
        board = pygame.image.load("assets/boards/" + board_type + ".png")
        board = pygame.transform.scale(board, (width, height))
        return board
    except pygame.error:
        # Fallback to a solid color surface if image not found
        surf = pygame.Surface((width, height))
        surf.fill((100, 100, 100))
        return surf


def load_pieces(piece_type, size):
    names = ['bb', 'bk', 'bn', 'bp', 'bq', 'br', 'wb', 'wk', 'wn', 'wp', 'wq', 'wr']
    pieces = {}
    for name in names:
        try:
            path = "assets/pieces/" + piece_type + '/' + name + ".png"
            pieces[name] = pygame.image.load(path)
            pieces[name] = pygame.transform.smoothscale(pieces[name], (size, size))
        except pygame.error:
            # Create a placeholder if piece not found
            surf = pygame.Surface((size, size), pygame.SRCALPHA)
            pygame.draw.circle(surf, (200, 0, 0) if name.startswith('b') else (255, 255, 255), (size//2, size//2), size//2)
            pieces[name] = surf

    return pieces


class ThemeManager:
    def __init__(self, board_type, piece_type):
        self.board_type = board_type
        self.piece_type = piece_type
        self.tile_size = TILE_SIZE
        self.board_size = SIZE
        self.load_assets()

    def load_assets(self):
        self.board_image = load_board(self.board_type, self.board_size, self.board_size)
        self.piece_images = load_pieces(self.piece_type, self.tile_size)

    def set_board_theme(self, board_type):
        self.board_type = board_type
        self.board_image = load_board(self.board_type, self.board_size, self.board_size)

    def set_piece_theme(self, piece_type):
        self.piece_type = piece_type
        self.piece_images = load_pieces(self.piece_type, self.tile_size)

# Initial global theme manager instance
theme_manager = ThemeManager(BOARD_TYPE, PIECES_TYPE)
