import pygame
from constants import *

BOARD_TYPE = "8_bit"
PIECES_TYPE = "cases"

SIZE = 800
TILE_SIZE = SIZE // 8

def load_board(board_type, width, height):
    board = pygame.image.load("chess.com-boards-and-pieces/boards/" + board_type + ".png")
    board = pygame.transform.scale(board, (width, height))
    return board

def load_pieces(piece_type, size):
    names = ['bb', 'bk', 'bn', 'bp', 'bq', 'br', 'wb', 'wk', 'wn', 'wp', 'wq', 'wr']
    pieces = {}
    for name in names:
        pieces[name] = pygame.image.load("chess.com-boards-and-pieces/pieces/" + piece_type + '/' + name + ".png")
        pieces[name] = pygame.transform.smoothscale(pieces[name], (size, size))
    
    return pieces

PIECE_IMAGES = load_pieces(PIECES_TYPE, TILE_SIZE)
board = load_board(BOARD_TYPE, SIZE, SIZE)