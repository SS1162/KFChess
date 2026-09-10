import pytest
from unittest.mock import AsyncMock, MagicMock, patch


_VALID_BOARD = "Board:\nwK bK\nCommands:\n"
_INVALID_TOKEN_BOARD = "Board:\nwK xZ\nCommands:\n"


# --- _load_game_session ---

def test_load_game_session_default_file(tmp_path, monkeypatch):
    board_file = tmp_path / "board.txt"
    board_file.write_text(_VALID_BOARD)
    monkeypatch.setattr("sys.argv", ["server.py", str(board_file)])
    from server import _load_game_session
    session = _load_game_session()
    assert session is not None


def test_load_game_session_custom_file(tmp_path, monkeypatch):
    board_file = tmp_path / "custom.txt"
    board_file.write_text(_VALID_BOARD)
    monkeypatch.setattr("sys.argv", ["server.py", str(board_file)])
    from server import _load_game_session
    session = _load_game_session()
    assert session.board.get_token(0, 0) == "wK"


def test_load_game_session_missing_file_exits(tmp_path, monkeypatch):
    monkeypatch.setattr("sys.argv", ["server.py", str(tmp_path / "nonexistent.txt")])
    with pytest.raises(SystemExit) as exc_info:
        from server import _load_game_session
        _load_game_session()
    assert exc_info.value.code == 1


def test_load_game_session_invalid_board_exits(tmp_path, monkeypatch):
    board_file = tmp_path / "bad.txt"
    board_file.write_text(_INVALID_TOKEN_BOARD)
    monkeypatch.setattr("sys.argv", ["server.py", str(board_file)])
    with pytest.raises(SystemExit) as exc_info:
        from server import _load_game_session
        _load_game_session()
    assert exc_info.value.code == 1


# --- handler ---

@pytest.mark.asyncio
async def test_handler_registers_and_unregisters():
    ws = AsyncMock()
    ws.__aiter__ = MagicMock(return_value=iter([]))
    cm = AsyncMock()
    gs = MagicMock()
    pr = MagicMock()

    from server import handler
    await handler(ws, connection_manager=cm, game_session=gs, player_registry=pr)

    cm.register.assert_awaited_once_with(ws)
    cm.unregister.assert_awaited_once_with(ws)
    pr.unregister.assert_called_once_with(ws)


@pytest.mark.asyncio
async def test_handler_broadcasts_command_result():
    import json
    ws = AsyncMock()
    ws.__aiter__ = MagicMock(return_value=iter([json.dumps({"type": "command", "raw": "wait 100"})]))
    cm = AsyncMock()
    gs = MagicMock(apply_command=MagicMock(return_value={"type": "state"}))
    pr = MagicMock()

    from server import handler
    await handler(ws, connection_manager=cm, game_session=gs, player_registry=pr)

    gs.apply_command.assert_called_once_with({"type": "command", "raw": "wait 100"})
    cm.broadcast.assert_awaited_once_with({"type": "state"})


@pytest.mark.asyncio
async def test_handler_unregisters_on_exception():
    ws = AsyncMock()

    async def _raise():
        raise RuntimeError("boom")
        yield  # make it an async generator

    ws.__aiter__ = MagicMock(return_value=_raise())
    cm = AsyncMock()
    gs = MagicMock()
    pr = MagicMock()

    from server import handler
    with pytest.raises(RuntimeError):
        await handler(ws, connection_manager=cm, game_session=gs, player_registry=pr)

    cm.unregister.assert_awaited_once_with(ws)
    pr.unregister.assert_called_once_with(ws)
