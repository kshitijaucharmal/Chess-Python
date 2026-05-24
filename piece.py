import pygame
from loader import PIECE_IMAGES, TILE_SIZE

class Piece:
    def __init__(self):
        self.unselect_jobs = False
        self.pos = pygame.Vector2()
        self.old_pos = pygame.Vector2()
        self.initialized = False
        self.piece_img = None
        self.piece_name = None
        self.selected = False
        self.white = True

    def init(self, piece_name, x, y):
        self.initialized = True
        self.piece_name = piece_name
        self.piece_img = PIECE_IMAGES[self.piece_name]
        self.pos = pygame.Vector2(x, y)
        self.old_pos = self.pos

        self.white = True if self.piece_name[0] == 'w' else False
        pass

    def deinit(self):
        self.initialized = False
        self.unselect_jobs = False
        self.pos = None
        self.old_pos = None
        self.piece_img = None
        self.piece_name = None
        self.selected = False
        pass

    def select(self):
        self.old_pos = self.pos.copy()
        self.selected = True

    def unselect(self):
        self.selected = False
        self.unselect_jobs = True

    def update(self, mouse_pos):
        if not self.initialized:
            return

        if self.selected:
            self.pos.update(mouse_pos[0] - TILE_SIZE/2, mouse_pos[1] - TILE_SIZE/2)

        if self.unselect_jobs:
            # if not valid position
            self.pos = self.old_pos

            # Done
            self.unselect_jobs = False

    def show(self, screen):
        if not self.initialized:
            return

        screen.blit(self.piece_img, self.pos)