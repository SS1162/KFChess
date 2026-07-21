import pytest
from unittest.mock import AsyncMock, MagicMock, patch, mock_open


# --- _load_game_session ---

def _mock_parse_result():
    return ([["wK", "bK"]], None)


@patch("server.sys.argv", ["server.py"])
@patch("server.BoardValidator.validate")
@patch("server.TextBoardParser")
def test_load_game_session_default_file(mock_parser_cls, mock_validate):
    mock_parser_cls.return_value.parse.return_value = _mock_parse_result()
    with patch("builtins.open", mock_open(read_data="")):
        from server import _load_game_session
        session = _load_game_session()
    assert session is not None
    mock_validate.assert_called_once()


@patch("server.sys.argv", ["server.py", "custom.txt"])
@patch("server.BoardValidator.validate")
@patch("server.TextBoardParser")
def test_load_game_session_custom_file(mock_parser_cls, mock_validate):
    mock_parser_cls.return_value.parse.return_value = _mock_parse_result()
    with patch("builtins.open", mock_open(read_data="")) as m:
        from server import _load_game_session
        _load_game_session()
    m.assert_called_once_with("custom.txt")


@patch("server.sys.argv", ["server.py"])
@patch("server.sys.exit")
def test_load_game_session_missing_file_exits(mock_exit):
    with patch("builtins.open", side_effect=OSError("not found")):
        from server import _load_game_session
        _load_game_session()
    mock_exit.assert_called_once_with(1)


@patch("server.sys.argv", ["server.py"])
@patch("server.sys.exit")
@patch("server.TextBoardParser")
def test_load_game_session_invalid_board_exits(mock_parser_cls, mock_exit):
    from exceptions import BoardError
    mock_parser_cls.return_value.parse.return_value = _mock_parse_result()
    with patch("builtins.open", mock_open(read_data="")):
        with patch("server.BoardValidator.validate", side_effect=BoardError("bad")):
            from server import _load_game_session
            _load_game_session()
    mock_exit.assert_called_once_with(1)


# --- handler ---

@pytest.mark.asyncio
async def test_handler_registers_and_unregisters():
    ws = AsyncMock()
    ws.__aiter__ = MagicMock(return_value=iter([]))
    cm = AsyncMock()
    gs = MagicMock()

    from server import handler
    await handler(ws, connection_manager=cm, game_session=gs)

    cm.register.assert_awaited_once_with(ws)
    cm.unregister.assert_awaited_once_with(ws)


@pytest.mark.asyncio
async def test_handler_broadcasts_command_result():
    ws = AsyncMock()
    ws.__aiter__ = MagicMock(return_value=iter(["wait 100"]))
    cm = AsyncMock()
    gs = MagicMock(apply_command=MagicMock(return_value={"type": "state"}))

    from server import handler
    await handler(ws, connection_manager=cm, game_session=gs)

    gs.apply_command.assert_called_once_with("wait 100")
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

    from server import handler
    with pytest.raises(RuntimeError):
        await handler(ws, connection_manager=cm, game_session=gs)

    cm.unregister.assert_awaited_once_with(ws)
