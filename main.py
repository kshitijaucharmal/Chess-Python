from pprint import pprint

import pygame
import pygame_gui
from pygame_gui.elements import UIProgressBar
from piece import Piece

from loader import board
from fen_loader import generate_board_from_fen
from constants import *

pygame.init()

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Chess Game")

manager = pygame_gui.UIManager((SCREEN_WIDTH, SCREEN_HEIGHT), theme_path="theme.json")

clock = pygame.time.Clock()
run = True

position = generate_board_from_fen(FEN)

hello_button = pygame_gui.elements.UIButton(relative_rect=pygame.Rect((SIZE, 0), (100, 50)),
                                            text='Say Hello',
                                            manager=manager)

bar = UIProgressBar(
    relative_rect=pygame.Rect(SIZE, 50, 300, 30),
    manager=manager
)
bar.status_percentage = 0.75

def draw_grid(screen):
    screen.blit(board, (START_X, START_Y))

chessboard = [[Piece() for i in range(8)] for j in range(8)]

def load_position():
    for i in range(len(position)):
        piece = position[i]

        x = START_X + (i % 8) * TILE_SIZE
        y = START_Y + (i // 8) * TILE_SIZE

        if piece == 'x':
            continue

        chessboard[i % 8][i // 8].init(piece, x, y)
    pass

def draw_pieces(screen):
    for i in range(8):
        for j in range(8):
            chessboard[i][j].show(screen)

load_position()
selected = None

while run:
    time_delta = clock.tick(60) / 1000.0
    mouse_pos = pygame.mouse.get_pos()

    for event in pygame.event.get():
        # Required for events
        x = mouse_pos[0] // TILE_SIZE
        y = mouse_pos[1] // TILE_SIZE

        file = chr(x + ord('a'))
        rank = str(8 - y)

        if event.type == pygame.QUIT:
            run = False

        if event.type == pygame.MOUSEBUTTONDOWN:
            # Left click
            if event.button == 1:
                if selected is None:
                    chessboard[x][y].select()
                    selected = chessboard[x][y]

        if event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                if selected is not None:
                    # Nothing on the square
                    if not chessboard[x][y].initialized and selected.piece_name is not None:
                        chessboard[x][y].init(selected.piece_name, x * TILE_SIZE, y * TILE_SIZE)
                        selected.deinit()
                    else:
                        # Own piece
                        if chessboard[x][y].white == selected.white:
                            selected.unselect()
                        # Capture
                        else:
                            chessboard[x][y].deinit()
                            chessboard[x][y].init(selected.piece_name, x * TILE_SIZE, y * TILE_SIZE)
                            selected.deinit()

                    selected = None

        # UI Events
        manager.process_events(event)

        if event.type == pygame_gui.UI_BUTTON_PRESSED:
            if event.ui_element == hello_button:
                print('Hello World!')


    # Continuous uodating
    for i in range(8):
        for j in range(8):
            chessboard[i][j].update(mouse_pos)

    manager.update(time_delta)

    screen.fill(BACKGROUND)
    
    draw_grid(screen)
    draw_pieces(screen)
    manager.draw_ui(screen)

    pygame.display.update()
    
pygame.quit()
