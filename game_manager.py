import uuid
from typing import Any

from bus_factory import build_bus
from game_loader import load_game_state
from game_session import GameSession


class GameManager:
    def __init__(self) -> None:
        self._games: dict[str, GameSession] = {}
        self._player_game: dict[Any, str] = {}

    def create_game(self, player_a, player_b, board_path: str) -> str:
        state = load_game_state(board_path)
        session = GameSession(state, build_bus())
        game_id = uuid.uuid4().hex
        self._games[game_id] = session
        self._player_game[player_a] = game_id
        self._player_game[player_b] = game_id
        return game_id

    def get_session_for_player(self, player_id) -> GameSession | None:
        game_id = self._player_game.get(player_id)
        return self._games.get(game_id) if game_id else None

    def get_players_in_game(self, game_id) -> list:
        return [p for p, gid in self._player_game.items() if gid == game_id]

    def end_game(self, game_id) -> None:
        self._games.pop(game_id, None)
        self._player_game = {p: gid for p, gid in self._player_game.items() if gid != game_id}
