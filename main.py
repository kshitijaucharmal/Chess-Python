from typing import Self

import pygame
import pygame_gui
from pygame_gui.elements import UIProgressBar, UILabel

from board_manager import BoardManager
from constants import *

pygame.init()

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Chess Game")

manager = pygame_gui.UIManager((SCREEN_WIDTH, SCREEN_HEIGHT), theme_path="theme.json")

clock = pygame.time.Clock()
run = True

hello_button = pygame_gui.elements.UIButton(relative_rect=pygame.Rect((SIZE, 0), (100, 50)),
                                            text='Say Hello',
                                            manager=manager)
status_bar = UILabel(relative_rect=pygame.Rect((SIZE, SCREEN_HEIGHT-50), (SCREEN_WIDTH - SIZE, 50)),manager=manager, text="Game Started")

bar = UIProgressBar(
    relative_rect=pygame.Rect(SIZE, 50, 300, 30),
    manager=manager
)
bar.status_percentage = 0.75

board = BoardManager()

while run:
    time_delta = clock.tick(60) / 1000.0
    mouse_pos = pygame.mouse.get_pos()

    # Required for events
    x = mouse_pos[0] // TILE_SIZE
    y = mouse_pos[1] // TILE_SIZE

    inside_board = 0 <= x < 8 and 0 <= y < 8

    if inside_board:
        board.mousex = x
        board.mousey = y

    file = chr(x + ord('a'))
    rank = str(8 - y)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            run = False

        if event.type == pygame.MOUSEBUTTONDOWN:
            # Left click (Start Selecting)
            if event.button == 1 and inside_board:
                board.start_selecting()

        if event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1 and inside_board:
                board.move_piece()

        # UI Events
        status_bar.set_text("White to move" if board.white_turn else "Black to move")
        manager.process_events(event)

        if event.type == pygame_gui.UI_BUTTON_PRESSED:
            if event.ui_element == hello_button:
                print('Hello World!')


    # Continuous uodating
    board.update(mouse_pos)
    manager.update(time_delta)

    screen.fill(BACKGROUND)

    board.draw(screen)
    manager.draw_ui(screen)

    pygame.display.update()
    
pygame.quit()
