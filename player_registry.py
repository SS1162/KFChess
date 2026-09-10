import constants


class GameFullError(Exception):
    pass


class PlayerRegistry:
    def __init__(self):
        self._players = {}

    def register(self, websocket, username: str) -> str:
        if len(self._players) >= 2:
            raise GameFullError("Game is full")
        color = constants.WHITE if len(self._players) == 0 else constants.BLACK
        self._players[websocket] = {"username": username, "color": color}
        return color

    def unregister(self, websocket) -> None:
        self._players.pop(websocket, None)

    def get_player(self, websocket) -> dict | None:
        return self._players.get(websocket)
