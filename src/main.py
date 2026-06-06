import pygame
import pygame_gui
import os
import chess
import chess.pgn
import time
import math
import random
import io
from pygame_gui.elements import UIProgressBar, UILabel, UITextBox, UITextEntryLine, UISelectionList, UIHorizontalSlider, UIButton, UIPanel
from pygame_gui.windows import UIConfirmationDialog, UIFileDialog

from src.ui.board_manager import BoardManager
from src.constants import *
from src.ui.loader import theme_manager
from src.engine.stockfish_manager import StockfishEngine
from src.engine.ai_explainer import AIExplainer

# --- App States ---
STATE_MENU = 0
STATE_SIDE_SELECT = 1
STATE_GAME = 2

# --- Game Modes ---
MODE_ANALYSIS = 0
MODE_BOT = 1

def format_eval(info):
    if not info: return "Evaluating..."
    score = info.get("score")
    if score:
        ws = score.white()
        if ws.is_mate(): return f"Mate in {abs(ws.mate())}"
        else:
            cp = ws.score()
            if cp is not None: return f"{cp/100.0:+.2f}"
    return "???"

def generate_move_history_html(board):
    """Generate a minimalist, high-fidelity move list."""
    html = "<font color='#888888' size=3><b>GAME RECORD</b></font><br><br>"
    moves = board.master_board.move_stack
    temp_board = chess.Board(board.start_fen)
    
    for i in range(0, len(moves), 2):
        move_num = i // 2 + 1
        
        # White
        white_move = moves[i]
        san_white = temp_board.san(white_move)
        temp_board.push(white_move)
        
        # Black
        san_black = ""
        if i + 1 < len(moves):
            black_move = moves[i+1]
            san_black = temp_board.san(black_move)
            temp_board.push(black_move)
        
        # Column 1: Move Number (Muted)
        m_num = f"<font color='#666666'>{move_num}.</font>"
        
        # Column 2: White Move (Bold, High Contrast)
        # We use &nbsp; for precise spacing and removed blocky background
        w_move = f"<b><a href='{i+1}'>{san_white}</a></b>"
        
        # Column 3: Black Move (Normal Weight)
        b_move = f"<a href='{i+2}'>{san_black}</a>" if san_black else ""
        
        # Calculate padding for perfect alignment
        # Approximate 10 non-breaking spaces for move column
        pad = "&nbsp;" * (max(2, 12 - len(san_white)))
        
        html += f"{m_num}&nbsp;&nbsp;{w_move}{pad}{b_move}<br>"
        
    return html

def draw_eval_bar(screen, current_cp, is_mate, mate_val):
    ratio = 1 / (1 + math.exp(-0.00368 * current_cp))
    wh = int(SIZE * ratio); bh = SIZE - wh
    bx, bw = SIZE, EVAL_BAR_WIDTH
    pygame.draw.rect(screen, EVAL_BLACK, (bx, 0, bw, bh))
    pygame.draw.rect(screen, EVAL_WHITE, (bx, bh, bw, wh))
    font = pygame.font.SysFont('Arial', 16, bold=True)
    if is_mate:
        sv = abs(mate_val); ts1 = f"M{sv}" if mate_val < 0 else ""; ts2 = f"M{sv}" if mate_val > 0 else ""
    else:
        sv = abs(round(current_cp/100, 1)); ts1 = str(sv) if current_cp <= 0 else ""; ts2 = str(sv) if current_cp > 0 else ""
    if ts1:
        s = font.render(ts1, True, (255, 255, 255))
        screen.blit(s, s.get_rect(midtop=(bx + bw//2, 10)))
    if ts2:
        s = font.render(ts2, True, (0, 0, 0))
        screen.blit(s, s.get_rect(midbottom=(bx + bw//2, SIZE - 10)))

def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Chess AI Grandmaster")
    manager = pygame_gui.UIManager((SCREEN_WIDTH, SCREEN_HEIGHT), theme_path="assets/theme.json")
    clock = pygame.time.Clock()
    
    app_state = STATE_MENU
    game_mode = MODE_ANALYSIS
    user_side = chess.WHITE
    
    # --- Modern Main Menu ---
    menu_panel = UIPanel(relative_rect=pygame.Rect((0, 0), (SCREEN_WIDTH, SCREEN_HEIGHT)), manager=manager)
    UILabel(relative_rect=pygame.Rect((SCREEN_WIDTH//2-250, 100), (500, 60)), text="CHESS AI GRANDMASTER", manager=manager, container=menu_panel, object_id="@title_label")
    menu_btn_y, btn_w, btn_h, btn_gap = 240, 340, 55, 15
    start_analysis_btn = UIButton(relative_rect=pygame.Rect((SCREEN_WIDTH//2-170, menu_btn_y), (btn_w, btn_h)), text="🔍  Analysis Board", manager=manager, container=menu_panel)
    play_bot_btn = UIButton(relative_rect=pygame.Rect((SCREEN_WIDTH//2-170, menu_btn_y + (btn_h+btn_gap)), (btn_w, btn_h)), text="🤖  Play with Bot", manager=manager, container=menu_panel)
    import_pgn_btn = UIButton(relative_rect=pygame.Rect((SCREEN_WIDTH//2-170, menu_btn_y + 2*(btn_h+btn_gap)), (btn_w, btn_h)), text="📂  Import PGN", manager=manager, container=menu_panel)
    quit_btn = UIButton(relative_rect=pygame.Rect((SCREEN_WIDTH//2-170, menu_btn_y + 3*(btn_h+btn_gap)), (btn_w, btn_h)), text="✖  Quit Application", manager=manager, container=menu_panel)

    # --- Side Selection Panel ---
    side_panel = UIPanel(relative_rect=pygame.Rect((0, 0), (SCREEN_WIDTH, SCREEN_HEIGHT)), manager=manager, visible=False)
    UILabel(relative_rect=pygame.Rect((SCREEN_WIDTH//2-200, 150), (400, 50)), text="CHOOSE YOUR SIDE", manager=manager, container=side_panel)
    select_white_btn = UIButton(relative_rect=pygame.Rect((SCREEN_WIDTH//2-150, 250), (btn_w-40, btn_h)), text="⚪  WHITE", manager=manager, container=side_panel)
    select_black_btn = UIButton(relative_rect=pygame.Rect((SCREEN_WIDTH//2-150, 320), (btn_w-40, btn_h)), text="⚫  BLACK", manager=manager, container=side_panel)
    select_random_btn = UIButton(relative_rect=pygame.Rect((SCREEN_WIDTH//2-150, 390), (btn_w-40, btn_h)), text="🎲  RANDOM", manager=manager, container=side_panel)
    back_to_menu_btn = UIButton(relative_rect=pygame.Rect((SCREEN_WIDTH//2-150, 500), (btn_w-40, btn_h)), text="⬅  Back to Menu", manager=manager, container=side_panel)

    # --- Game UI ---
    PX = SIZE + EVAL_BAR_WIDTH + 15; PW = SCREEN_WIDTH - PX - 20
    game_container = UIPanel(relative_rect=pygame.Rect((PX, 0), (PW + 20, SCREEN_HEIGHT)), manager=manager, visible=False)
    status_bar = UILabel(relative_rect=pygame.Rect((0, 10), (PW, 30)), manager=manager, container=game_container, text="Ready")
    history_box = UITextBox(relative_rect=pygame.Rect((0, 50), (PW, 140)), html_text="<b>Move History:</b>", manager=manager, container=game_container)
    prev_btn = UIButton(relative_rect=pygame.Rect((0, 195), (PW // 2 - 5, 30)), text="< PREV", manager=manager, container=game_container)
    next_btn = UIButton(relative_rect=pygame.Rect((PW // 2 + 5, 195), (PW // 2 - 5, 30)), text="NEXT >", manager=manager, container=game_container)
    chat_box = UITextBox(relative_rect=pygame.Rect((0, 230), (PW, 170)), html_text="<b>AI Coach:</b> Welcome!", manager=manager, container=game_container)
    analyse_btn = UIButton(relative_rect=pygame.Rect((0, 405), (PW, 40)), text="ANALYSE POSITION", manager=manager, container=game_container)
    
    toggle_y = 455
    best_move_btn = UIButton(relative_rect=pygame.Rect((0, toggle_y), (PW // 2 - 5, 25)), text="Best Move: ON", manager=manager, container=game_container)
    threats_btn = UIButton(relative_rect=pygame.Rect((PW // 2 + 5, toggle_y), (PW // 2 - 5, 25)), text="Threats: OFF", manager=manager, container=game_container)
    annots_btn = UIButton(relative_rect=pygame.Rect((0, toggle_y + 30), (PW // 2 - 5, 25)), text="Manual: ON", manager=manager, container=game_container)
    flip_btn = UIButton(relative_rect=pygame.Rect((PW // 2 + 5, toggle_y + 30), (PW // 2 - 5, 25)), text="Flip Board", manager=manager, container=game_container)
    anim_btn = UIButton(relative_rect=pygame.Rect((0, toggle_y + 60), (PW, 30)), text="Animations: ON", manager=manager, container=game_container)
    
    depth_val_lbl = UILabel(relative_rect=pygame.Rect((PW - 40, toggle_y + 95), (40, 20)), manager=manager, container=game_container, text="12")
    UILabel(relative_rect=pygame.Rect((0, toggle_y + 95), (PW - 40, 20)), manager=manager, container=game_container, text="Engine Depth")
    depth_sld = UIHorizontalSlider(relative_rect=pygame.Rect((0, toggle_y + 115), (PW, 20)), start_value=12, value_range=(1, 24), manager=manager, container=game_container)

    boards, pieces = [f.replace('.png', '') for f in os.listdir('assets/boards') if f.endswith('.png')], sorted([d for d in os.listdir('assets/pieces') if os.path.isdir(os.path.join('assets/pieces', d))])
    board_list = UISelectionList(relative_rect=pygame.Rect((0, toggle_y + 145), (PW // 2, 70)), item_list=sorted(boards), manager=manager, container=game_container)
    piece_list = UISelectionList(relative_rect=pygame.Rect((PW // 2 + 5, toggle_y + 145), (PW // 2 - 5, 70)), item_list=pieces, manager=manager, container=game_container)
    return_btn = UIButton(relative_rect=pygame.Rect((0, SCREEN_HEIGHT - 40), (PW, 30)), text="Exit to Main Menu", manager=manager, container=game_container)

    # --- Init ---
    board, engine, ai_explainer = BoardManager(), StockfishEngine(), AIExplainer()
    run, last_fen, game_over_dialog, eval_at_pos = True, None, None, "0.00"
    target_cp, current_cp, is_mate, mate_val = 0, 0, False, 0
    thinking_timer, thinking_dots, file_dialog = 0.0, 0, None
    latest_info = None
    last_history_len = -1

    def start_game(mode, side=chess.WHITE, pgn_data=None):
        nonlocal app_state, game_mode, user_side, last_fen, last_history_len
        app_state = STATE_GAME; game_mode = mode; user_side = side
        start_fen = FEN
        moves_to_push = []
        if pgn_data:
            pgn = chess.pgn.read_game(io.StringIO(pgn_data))
            if pgn:
                start_fen = pgn.headers.get("FEN", FEN)
                moves_to_push = list(pgn.mainline_moves())
        
        board.reset(start_fen=start_fen)
        board.flipped = (user_side == chess.BLACK)
        for m in moves_to_push: board.master_board.push(m)
        board.set_view_ply(len(board.master_board.move_stack), animate=False)
        
        menu_panel.hide(); side_panel.hide(); game_container.show(); last_fen = None; last_history_len = -1

    while run:
        time_delta = clock.tick(60) / 1000.0
        mouse_pos = pygame.mouse.get_pos()
        if app_state == STATE_GAME:
            current_fen = board.board.fen()
            if current_fen != last_fen:
                engine.analyze(board.board, depth=int(depth_sld.get_current_value()))
                last_fen = current_fen
            
            # Only update HTML when the game history actually changes
            if len(board.master_board.move_stack) != last_history_len:
                last_history_len = len(board.master_board.move_stack)
                history_box.html_text = generate_move_history_html(board); history_box.rebuild()
                if board.view_ply == last_history_len and history_box.scroll_bar:
                    history_box.scroll_bar.set_scroll_from_start_percentage(1.0)
            
            latest_info = engine.get_latest_info()
            if latest_info:
                score = latest_info.get("score")
                if score:
                    ws = score.white()
                    if ws.is_mate(): is_mate, mate_val, target_cp = True, ws.mate(), (10000 if ws.mate() > 0 else -10000)
                    else: is_mate, target_cp = False, ws.score() or 0
                eval_at_pos = format_eval(latest_info)
                board.best_move_suggestion = latest_info.get("pv")[0] if latest_info.get("pv") else None
                status_bar.set_text(f"Eval: {eval_at_pos} | Best: {board.best_move_suggestion.uci() if board.best_move_suggestion else '...'}")

            if game_mode == MODE_BOT and board.board.turn != user_side and not board.board.is_game_over() and board.view_ply == len(board.master_board.move_stack):
                if latest_info and latest_info.get("pv") and latest_info.get("depth", 0) >= int(depth_sld.get_current_value()):
                    board._execute_move(latest_info["pv"][0], animate=True)

            current_cp += (target_cp - current_cp) * min(1.0, time_delta * 5.0)
            if ai_explainer.is_thinking:
                thinking_timer += time_delta
                if thinking_timer > 0.4:
                    thinking_timer, thinking_dots = 0, (thinking_dots + 1) % 4
                    chat_box.html_text = f"<b>AI Coach:</b><br>Thinking{'.' * thinking_dots}"; chat_box.rebuild()
            ai_msg = ai_explainer.get_latest_explanation()
            if ai_msg:
                chat_box.html_text = ai_msg; chat_box.rebuild()
                if chat_box.scroll_bar: chat_box.scroll_bar.set_scroll_from_start_percentage(1.0)
            if board.board.is_game_over() and game_over_dialog is None:
                res = "White Wins!" if board.board.outcome().winner == chess.WHITE else ("Black Wins!" if board.board.outcome().winner == chess.BLACK else "Draw")
                game_over_dialog = UIConfirmationDialog(rect=pygame.Rect((SCREEN_WIDTH//2-150, SCREEN_HEIGHT//2-100), (300, 200)), manager=manager, action_long_desc=f"<b>Game Over!</b><br>{res}<br><br>Restart?", window_title="Game Over", blocking=True)

        depth_val_lbl.set_text(str(int(depth_sld.get_current_value())))
        for event in pygame.event.get():
            if event.type == pygame.QUIT: run = False
            if app_state == STATE_GAME:
                if event.type == pygame.MOUSEBUTTONDOWN: board.handle_click(event.pos, event.button)
                if event.type == pygame.MOUSEBUTTONUP: board.handle_release(event.pos, event.button)
            manager.process_events(event)
            if event.type == pygame_gui.UI_BUTTON_PRESSED:
                if event.ui_element == start_analysis_btn: game_mode = MODE_ANALYSIS; app_state = STATE_SIDE_SELECT; menu_panel.hide(); side_panel.show()
                elif event.ui_element == play_bot_btn: game_mode = MODE_BOT; app_state = STATE_SIDE_SELECT; menu_panel.hide(); side_panel.show()
                elif event.ui_element == import_pgn_btn: file_dialog = UIFileDialog(pygame.Rect(SCREEN_WIDTH//2-220, 50, 440, 500), manager, window_title='Load PGN', initial_file_path='.', allow_picking_directories=False)
                elif event.ui_element == select_white_btn: start_game(game_mode, chess.WHITE)
                elif event.ui_element == select_black_btn: start_game(game_mode, chess.BLACK)
                elif event.ui_element == select_random_btn: start_game(game_mode, random.choice([chess.WHITE, chess.BLACK]))
                elif event.ui_element == back_to_menu_btn: side_panel.hide(); menu_panel.show(); app_state = STATE_MENU
                elif event.ui_element == return_btn: game_container.hide(); menu_panel.show(); app_state = STATE_MENU
                elif event.ui_element == quit_btn: run = False
                elif event.ui_element == analyse_btn:
                    if len(board.board.move_stack) > 0:
                        lm = board.board.move_stack[-1]; pb = board.board.copy(); pb.pop()
                        ai_explainer.explain_move(pb, lm, eval_at_pos)
                elif event.ui_element == prev_btn: board.set_view_ply(board.view_ply - 1)
                elif event.ui_element == next_btn: board.set_view_ply(board.view_ply + 1)
                elif event.ui_element == flip_btn: board.flipped = not board.flipped; board.set_view_ply(board.view_ply)
                elif event.ui_element == best_move_btn: board.show_best_move = not board.show_best_move; best_move_btn.set_text(f"Best Move: {'ON' if board.show_best_move else 'OFF'}")
                elif event.ui_element == threats_btn: board.show_threats = not board.show_threats; threats_btn.set_text(f"Threats: {'ON' if board.show_threats else 'OFF'}")
                elif event.ui_element == annots_btn: board.show_annotations = not board.show_annotations; annots_btn.set_text(f"Manual: {'ON' if board.show_annotations else 'OFF'}")
                elif event.ui_element == anim_btn: board.enable_animations = not board.enable_animations; anim_btn.set_text(f"Anim: {'ON' if board.enable_animations else 'OFF'}")
            if event.type == pygame_gui.UI_TEXT_BOX_LINK_CLICKED and event.ui_element == history_box:
                board.set_view_ply(int(event.link_target))
            if event.type == pygame_gui.UI_FILE_DIALOG_PATH_PICKED:
                try:
                    with open(event.text, 'r') as f: start_game(MODE_ANALYSIS, chess.WHITE, f.read())
                except: pass
            if event.type == pygame_gui.UI_CONFIRMATION_DIALOG_CONFIRMED and event.ui_element == game_over_dialog:
                board.reset(); game_over_dialog = None; last_fen = None
        screen.fill(BACKGROUND)
        if app_state == STATE_GAME:
            board.update(mouse_pos, time_delta); board.draw(screen, mouse_pos); draw_eval_bar(screen, current_cp, is_mate, mate_val)
        manager.update(time_delta); manager.draw_ui(screen); pygame.display.update()
    engine.quit(); pygame.quit()

if __name__ == "__main__": main()
