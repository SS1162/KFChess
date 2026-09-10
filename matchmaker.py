class Matchmaker:
    def __init__(self) -> None:
        self._waiting: list[dict] = []

    def find_match(self, player_id, elo: int):
        for entry in self._waiting:
            if entry["player_id"] == player_id:
                continue
            if abs(entry["elo"] - elo) <= 100:
                self._waiting.remove(entry)
                return entry["player_id"]
        self._waiting.append({"player_id": player_id, "elo": elo})
        return None

    def remove(self, player_id) -> None:
        self._waiting = [e for e in self._waiting if e["player_id"] != player_id]

    def is_waiting(self, player_id) -> bool:
        return any(e["player_id"] == player_id for e in self._waiting)
