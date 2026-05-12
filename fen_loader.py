from curses.ascii import isdigit

import pygame
from pprint import  pprint

mappings = {
    'b': 'bb',
    'r': 'br',
    'k': 'bk',
    'n': 'bn',
    'p': 'bp',
    'q': 'bq',
    'B': 'wb',
    'R': 'wr',
    'K': 'wk',
    'N': 'wn',
    'P': 'wp',
    'Q': 'wq',
}

def generate_board_from_fen(fen_string):
    board = ['x'] * 64
    ind = 0
    
    position, active, castling, enpassant, half_move, full_move = fen_string.split()
    print("Position: ", position)
    print("Active: ", active)
    print("Castling: ", castling)
    print("En Passant: ", enpassant)
    print("Half Move: ", half_move)
    print("Full Move: ", full_move)
    
    # Interpret position
    for val in position:
        if val in mappings:
            board[ind] = mappings[val]
            ind += 1
        elif isdigit(val):
            ind += int(val)
        pass
    pass

    return board