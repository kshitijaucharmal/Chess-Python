from pprint import pprint

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
        self.loc = [1 + int(self.pos.x // TILE_SIZE), 8 - int(self.pos.y // TILE_SIZE)]

        self.valid_moves = []
        pass
    
    def calculate_valid_moves(self, board):
        if not self.initialized:
            return
        if self.piece_name[1] == 'p':
            print("Pawn")
            if self.piece_name[0] == 'w':
                # White moves forward
                move = [self.loc[0], self.loc[1]+1]
                self.valid_moves.append(move)
                pass
            else:
                move = [self.loc[0], self.loc[1]-1]
                self.valid_moves.append(move)
                pass
        if self.piece_name[1] == 'b':
            print("Bishop")
            x, y = self.loc

            directions = [
                (1, 1), (-1, -1), (1, -1), (-1, 1),  # Diagonals
            ]

            for dx, dy in directions:
                for i in range(1, 9):
                    nx = x + (i * dx)
                    ny = y + (i * dy)

                    if 1 <= nx <= 8 and 1 <= ny <= 8:
                        if board.chessboard[nx-1][8-ny].initialized:
                            if board.chessboard[nx - 1][8 - ny].white != self.white:
                                self.valid_moves.append([nx, ny])
                            break
                        self.valid_moves.append([nx, ny])
        if self.piece_name[1] == 'k':
            print("King")
            x, y = self.loc

            directions = [
                (1, 1), (-1, -1), (1, -1), (-1, 1),  # Diagonals
                (1, 0), (-1, 0), (0, 1), (0, -1)  # Straights (Horizontal & Vertical)
            ]

            for dx, dy in directions:
                nx = x + dx
                ny = y + dy

                if 1 <= nx <= 8 and 1 <= ny <= 8:
                    if board.chessboard[nx - 1][8 - ny].initialized:
                        if board.chessboard[nx - 1][8 - ny].white != self.white:
                            self.valid_moves.append([nx, ny])
                        continue
                    self.valid_moves.append([nx, ny])
        if self.piece_name[1] == 'q':
            print("Queen")
            x, y = self.loc

            directions = [
                (1, 1), (-1, -1), (1, -1), (-1, 1),  # Diagonals
                (1, 0), (-1, 0), (0, 1), (0, -1)  # Straights (Horizontal & Vertical)
            ]

            for dx, dy in directions:
                for i in range(1, 9):
                    nx = x + (i * dx)
                    ny = y + (i * dy)

                    if 1 <= nx <= 8 and 1 <= ny <= 8:
                        if board.chessboard[nx-1][8-ny].initialized:
                            if board.chessboard[nx - 1][8 - ny].white != self.white:
                                self.valid_moves.append([nx, ny])
                            break
                        self.valid_moves.append([nx, ny])
        if self.piece_name[1] == 'r':
            print("Rook")
            x, y = self.loc

            directions = [
                (1, 0), (-1, 0), (0, 1), (0, -1)  # Straights (Horizontal & Vertical)
            ]

            for dx, dy in directions:
                for i in range(1, 9):
                    nx = x + (i * dx)
                    ny = y + (i * dy)

                    if 1 <= nx <= 8 and 1 <= ny <= 8:
                        if board.chessboard[nx-1][8-ny].initialized:
                            if board.chessboard[nx - 1][8 - ny].white != self.white:
                                self.valid_moves.append([nx, ny])
                            break
                        self.valid_moves.append([nx, ny])

        if self.piece_name[1] == 'n':
            print("Knight")
            x, y = self.loc

            directions = [
                (1, 2), (1, -2), (-1, 2), (-1, -2),
                (2, 1), (2, -1), (-2, 1), (-2, -1)
            ]

            for dx, dy in directions:
                nx = x + dx
                ny = y + dy

                if 1 <= nx <= 8 and 1 <= ny <= 8:
                    if board.chessboard[nx - 1][8 - ny].initialized:
                        if board.chessboard[nx - 1][8 - ny].white != self.white:
                            self.valid_moves.append([nx, ny])
                        continue
                    self.valid_moves.append([nx, ny])
            pass
    
    def init(self, piece_name, x, y):
        self.initialized = True
        self.piece_name = piece_name
        self.piece_img = PIECE_IMAGES[self.piece_name]
        self.pos = pygame.Vector2(x, y)
        self.loc = [1 + int(self.pos.x // TILE_SIZE), 8 - int(self.pos.y // TILE_SIZE)]
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
        self.loc = []
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
            self.loc = [1 + int(self.pos.x // TILE_SIZE), 8 - int(self.pos.y // TILE_SIZE)]

            # Done
            self.unselect_jobs = False

    def show(self, screen):
        if not self.initialized:
            return

        screen.blit(self.piece_img, self.pos)