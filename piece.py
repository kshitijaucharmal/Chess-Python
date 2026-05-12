import pygame
from fen_loader import mappings

class Piece:
    def __init__(self, piece_type):
        self.piece_name = mappings[piece_type]
        pass
    
    def show(self, screen, x, y):
        screen.blit(self.piece_name, (x, y))
