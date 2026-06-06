import chess.engine
import threading
import queue

class StockfishEngine:
    def __init__(self, path="/usr/bin/stockfish"):
        self.path = path
        self.engine = None
        self.result_queue = queue.Queue()
        self.analysis_thread = None
        self.stop_signal = False
        self._start_engine()

    def _start_engine(self):
        try:
            self.engine = chess.engine.SimpleEngine.popen_uci(self.path)
        except Exception as e:
            print(f"Failed to start Stockfish: {e}")

    def analyze(self, board, depth=12):
        """Starts an asynchronous analysis of the current board state."""
        self.stop_analysis()
        self.stop_signal = False
        self.analysis_thread = threading.Thread(target=self._run_analysis, args=(board.copy(), depth))
        self.analysis_thread.start()

    def _run_analysis(self, board, depth):
        try:
            with self.engine.analysis(board, chess.engine.Limit(depth=depth)) as analysis:
                for info in analysis:
                    if self.stop_signal:
                        break
                    self.result_queue.put(info)
        except Exception as e:
            print(f"Analysis error: {e}")

    def stop_analysis(self):
        self.stop_signal = True
        # Do not join() here as it blocks the main thread
        # The thread will exit on its next iteration
        self.analysis_thread = None
        # Clear the queue
        while not self.result_queue.empty():
            try:
                self.result_queue.get_nowait()
            except queue.Empty:
                break

    def get_latest_info(self):
        """Returns the most recent info from the queue."""
        latest = None
        while not self.result_queue.empty():
            latest = self.result_queue.get()
        return latest

    def get_best_move(self, board, time_limit=0.1):
        """Synchronous call to get the best move."""
        try:
            result = self.engine.play(board, chess.engine.Limit(time=time_limit))
            return result.move
        except:
            return None

    def quit(self):
        self.stop_analysis()
        if self.engine:
            self.engine.quit()
