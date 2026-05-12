import pygame
import pygame_gui
from pygame_gui.elements import UIProgressBar
from piece import Piece

from loader import load_board, load_pieces
from fen_loader import generate_board_from_fen

pygame.init()

# Constants ----------------------------------------

SCREEN_WIDTH = 1200
SCREEN_HEIGHT = 800

SIZE = 800

BOARD_TYPE = "icy_sea"
PIECES_TYPE = "icy_sea"

TILE_SIZE = SIZE // 8
START_X = 0
START_Y = 0

FEN = 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1'
# FEN = '2k1r3/2Q5/pp5p/6p1/8/P2rq3/P1R3BP/1R3K2 b - - 0 25'
# FEN = '1r6/5pp1/R1R4p/1r1pP3/2pkQPP1/7P/1P6/2K5 w - - 0 41'

board = load_board(BOARD_TYPE, SIZE, SIZE)
pieces = load_pieces(PIECES_TYPE, TILE_SIZE)

# Colors
BACKGROUND = (48, 46, 43)

# Constants ----------------------------------------

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
    
def draw_pieces():
    for i in range(len(position)):
        piece = position[i]
        if piece == 'x':
            continue
        piece_name = pieces[piece]
        x = START_X + (i % 8) * TILE_SIZE
        y = START_Y + (i // 8) * TILE_SIZE
        screen.blit(piece_name, (x, y))
    pass

while run:
    time_delta = clock.tick(60) / 1000.0
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            run = False

        manager.process_events(event)

        if event.type == pygame_gui.UI_BUTTON_PRESSED:
            if event.ui_element == hello_button:
                print('Hello World!')

    manager.update(time_delta)

    screen.fill(BACKGROUND)
    
    draw_grid(screen)
    draw_pieces()
    manager.draw_ui(screen)

    pygame.display.update()
    
pygame.quit()





