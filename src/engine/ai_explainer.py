import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
import threading
import queue

load_dotenv()

class AIExplainer:
    def __init__(self):
        self.api_key = os.getenv("MISTRAL_API_KEY")
        self.model_name = "mistral-medium-latest"
        self.base_url = "https://api.mistral.ai/v1"
        self.client = None
        self.result_queue = queue.Queue()
        self._is_thinking = False
        self._setup_client()

    def _setup_client(self):
        if not self.api_key:
            return
        self.client = ChatOpenAI(
            base_url=self.base_url,
            api_key=self.api_key,
            model=self.model_name,
            temperature=0.7
        )

    @property
    def is_thinking(self):
        return self._is_thinking

    def explain_move(self, board, move, evaluation):
        """Asynchronously get an explanation for a move."""
        if not self.client:
            self.result_queue.put("<font color='#E71C24'><b>AI Error:</b> Mistral API key not configured in .env file.</font>")
            return

        self._is_thinking = True
        thread = threading.Thread(target=self._query_ai, args=(board.fen(), move.uci(), evaluation))
        thread.start()

    def _query_ai(self, fen, move_uci, evaluation):
        try:
            system_prompt = (
                "You are an elite chess grandmaster and coach. "
                "Analyze the position and the move. "
                "Provide a highly concise (max 2 sentences) explanation of WHY the move is good or bad. "
                "Focus on the immediate tactical or positional impact (e.g., controlling the center, developing a piece, or creating a threat). "
                "Format using basic HTML: "
                "Use <b>bold</b> for moves and key tactical terms. "
                "Use <font color='#81B64C'>Green</font> for positive results and <font color='#E71C24'>Red</font> for blunders/negatives. "
                "Do not use markdown headers or lists. Just plain text with HTML tags."
            )
            
            user_prompt = (
                f"Position: {fen}\n"
                f"Move Played: {move_uci}\n"
                f"Engine Eval: {evaluation}\n\n"
                "Why was this move made?"
            )

            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt)
            ]

            response = self.client.invoke(messages)
            # Ensure the response is properly wrapped for the chatbox
            content = response.content.replace('\n\n', '<br><br>')
            formatted_response = f"<b>AI Coach:</b><br>{content}"
            self.result_queue.put(formatted_response)
        except Exception as e:
            self.result_queue.put(f"<font color='#E71C24'><b>AI Error:</b> {str(e)}</font>")
        finally:
            self._is_thinking = False

    def get_latest_explanation(self):
        """Returns the most recent explanation from the queue."""
        try:
            return self.result_queue.get_nowait()
        except queue.Empty:
            return None
