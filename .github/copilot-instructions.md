# KFChess — Coding Agent Instructions

## Project overview

KFChess started as a single-process, real-time chess engine that reads a
text-based board + command stream from stdin (`main.py`) and mutates game
state in response to click, jump, wait, and print commands. It has since
grown a **websocket multiplayer server layer** (`server.py` and friends) that
wraps the same engine so two browser/CLI clients can play against each other
over the network with accounts and Elo. There is no GUI; both the offline
engine and the server are exercised through tests, stdin piping, and
websocket messages.

## Tech stack

- **Language**: Python 3
- **Runtime dependencies**: `websockets` (server only), stdlib `sqlite3`
  (accounts). The offline engine (`main.py`) has no third-party dependencies.
- **Test runner**: `pytest` (install with `pip install pytest websockets` if
  missing; no `requirements.txt`)
- **No build step**: run tests directly with `pytest` from the repo root

## Repository layout — two entry points, one engine

```
/                        ← project root (also sys.path root for imports)
├── main.py              ← OFFLINE entry point: stdin → registries → GameState loop
├── server.py            ← ONLINE entry point: websocket server wrapping the same engine
│
│  ── core engine (used by both entry points) ──
├── board.py             ← Board dataclass (grid mutation)
├── game_state.py        ← mutable engine state (clock, in-flight, airborne, status)
├── game_status.py       ← GameStatus enum + GameOverRegistry
├── movement.py          ← per-piece move validators + MoveValidator registry
├── coordinate_translator.py  ← pixel → BoardPosition conversion
├── parser.py            ← TextBoardParser (stdin) + CommandParser (registry)
├── command_executor.py  ← CommandExecutor registry
├── commands.py          ← frozen command dataclasses (Click/Jump/Wait/Print)
├── models.py            ← frozen value objects (Point, BoardPosition, Move)
├── constants.py         ← CELL_SIZE, TIME_PER_CELL_MS, JUMP_DURATION_MS, WHITE/BLACK, …
├── exceptions.py        ← BoardError / CommandError hierarchies
├── validator.py         ← BoardValidator (structural grid checks)
├── engine_factory.py    ← builds+wires MoveValidator/CommandParser/CommandExecutor
├── game_loader.py       ← reads a board file → validated GameState (used by GameManager)
├── handlers/            ← one module per command: click, jump, wait, print_board
│   └── *.py             ← each exports parse_<cmd> and handle_<cmd>
│
│  ── server / multiplayer layer (server.py and its collaborators) ──
├── connection_manager.py← tracks websocket clients, register/unregister/broadcast/send_to
├── protocol.py          ← wire message dataclasses (JoinRequest/JoinAck/StateUpdate/ErrorMessage) + parse/serialize
├── engine_adapter.py    ← run_single_command(state, raw): parses+executes one raw command against a GameState
├── game_session.py      ← per-game object: protocol in → engine_adapter → bus publish → protocol out
├── bus.py / bus_factory.py ← tiny pub/sub Bus; build_bus() wires "move_made" → move_logger.log_move
├── move_logger.py       ← bus subscriber that logs each move to kfchess.log
├── account_service.py   ← AccountService: sqlite-backed signup/login, password hashing, Elo storage
├── player_registry.py   ← PlayerRegistry: assigns WHITE/BLACK to the first 2 websockets that join
├── matchmaker.py        ← Matchmaker: Elo-based waiting-pool matcher (not yet wired into server.py)
├── game_manager.py      ← GameManager: multi-game registry keyed by uuid game_id (not yet wired into server.py)
├── starting_position.txt← default board file loaded by server.py
│
├── conftest.py          ← adds repo root to sys.path (required for test imports)
└── tests/               ← pytest test files (test_*.py, one per module above)
```

**Current wiring caveat**: `server.py` today runs a **single** global
`GameSession` shared by all connected clients (via `ConnectionManager`
broadcast) and uses `PlayerRegistry` to cap it at 2 players. `GameManager` and
`Matchmaker` exist with their own tests but are **not yet called from
`server.py`** — they are the building blocks for multi-room/matchmaking
support, not currently-active code paths. Don't assume they're wired in
without checking `server.py` first.

## Architecture: registry / factory / adapter patterns

Every extensible subsystem uses the same registry pattern — **never modify
the registry class itself to add a new entry**:

| Registry class    | Key type     | Registered in       |
|-------------------|--------------|----------------------|
| `CommandParser`   | keyword str  | `engine_factory.py`  |
| `CommandExecutor` | command type | `engine_factory.py`  |
| `MoveValidator`   | piece letter | `engine_factory.py`  |
| `GameOverRegistry`| token str    | `game_status.py`     |

`main.py` and `engine_adapter.py` (used by the server) both call into
`engine_factory.build_command_parser()` / `build_executor()` rather than
duplicating registration — **this is the single source of truth for wiring
the engine**; do not re-register handlers elsewhere.

To add a new command: create a `commands.py` dataclass, add `parse_*` /
`handle_*` in `handlers/`, and register both in `engine_factory.py`.

## Server layer control flow

A client message travels: `server.py` websocket handler → deserialize JSON →
`protocol.py` (validates message shape, raises `ProtocolError`) → for
`"join"` messages: `account_service.AccountService.login_or_register` (sqlite
auth/Elo) then `player_registry.PlayerRegistry.register` (assigns
WHITE/BLACK, raises `GameFullError` past 2 players) → for `"command"`
messages: `game_session.GameSession.apply_command` → `engine_adapter.py`
(`run_single_command`, reuses the core engine registries) → on success,
`bus.Bus.publish("move_made", …)` (currently subscribed by
`move_logger.log_move`) → `protocol.serialize_state` → broadcast to all
clients via `connection_manager.ConnectionManager`.

Each layer defines and raises its **own** exception type locally rather than
extending `exceptions.py`'s `BoardError`/`CommandError` hierarchy:
`protocol.ProtocolError`, `account_service.AccountError`,
`player_registry.GameFullError`. `server.py`'s handler catches these at the
message-dispatch level and turns them into `protocol.ErrorMessage` replies —
it never lets them propagate and crash the connection.

## Wire protocol (`protocol.py`)

Messages are JSON dicts with a `type` field, dataclass-backed on both ends:

| `type`     | Direction       | Dataclass       | Notes |
|------------|------------------|-----------------|-------|
| `join`     | client → server  | `JoinRequest`   | `username` + `password`; triggers login-or-register |
| `joined`   | server → client  | `JoinAck`       | echoes `username`, assigned `color`, current `elo` |
| `command`  | client → server  | `IncomingCommand` | `raw` is the same command string the offline engine parses (e.g. `click ...`) |
| `state`    | server → clients | `StateUpdate`   | full `board` grid + `status` name; **no turn/current-player field** — KFChess is real-time with concurrent async moves, there is no turn concept |
| `error`    | server → client  | `ErrorMessage`  | `reason` string; sent on malformed JSON, `ProtocolError`, `AccountError`, or `GameFullError` |

`parse_join` / `parse_incoming` validate shape and raise `ProtocolError` on
anything malformed; `serialize_state` is the only way a `GameState` should be
turned into wire JSON.

## Accounts, players, and Elo

- Accounts are **persisted** in a local sqlite file (`accounts.db`) via
  `account_service.AccountService`; passwords are salted + SHA-256 hashed
  (`salt$digest`), compared with `hmac.compare_digest`. Never store or log raw
  passwords.
- `login_or_register` creates the account on first sight of a username,
  otherwise authenticates — there is no separate signup flow exposed over the
  wire.
- Elo is stored per-account in sqlite (`elo` column, default 1200) but nothing
  currently updates it after a game ends — Elo adjustment is not implemented
  yet.
- Player-to-color assignment (`player_registry.PlayerRegistry`) is **in-memory
  only**, keyed by the live websocket object, and reset when the process
  restarts — it is unrelated to account persistence.

## Key domain rules

- Board tokens: `'.'` (empty) or `<color><piece>` e.g. `wK`, `bQ`
  (`ALLOWED_TOKENS` in `constants.py`).
- `BoardPosition(row, col)` is the internal coordinate; pixel coordinates are
  converted via `coordinate_translator.pixel_to_board`.
- Moves are **asynchronous**: `schedule_move` puts a piece in-flight;
  `apply_arrivals` (called by `handle_wait`) commits it. The piece stays at its
  origin on the board until arrival.
- Jumps make a piece **airborne** for `JUMP_DURATION_MS` ms; airborne pieces
  can air-capture arriving enemies.
- `GameState.status` is checked before scheduling any move or jump; ignore the
  action silently if not `PLAYING`.

## Running tests

```bash
pytest                  # run all tests from repo root
pytest tests/test_game_state.py   # single file
```

`conftest.py` handles `sys.path`; no `PYTHONPATH` export is needed.

## Established test conventions (see `.github/instructions/tests.instructions.md`)

- Pure unit tests only; no monkeypatching.
- AAA (Arrange-Act-Assert) structure.
- Prefer `@pytest.mark.parametrize` over duplicated test functions.
- Avoid combinatorial explosion — target minimum tests for full branch coverage.
- Helper factories (`_state(token_rows)`, `_handler()`) are defined at module
  level in each test file; follow the same pattern when adding tests.

## Common pitfalls

- All imports use **bare module names** (`from board import Board`), not package
  paths. This works because `conftest.py` inserts the repo root into `sys.path`.
  Do not introduce package `__init__.py` files at the root level.
- `Board` is a `@dataclass` but is **mutable** by design (`apply_move`,
  `set_token`). Do not add `frozen=True`.
- `MoveContext.board` holds a reference to the live board; validators read it
  directly — do not copy the board before passing it.
- Logging goes to `kfchess.log`, but `main.py` and `server.py` each call
  `logging.basicConfig` independently (WARNING vs. INFO level) since they are
  separate entry points — `basicConfig` only takes effect on its first call in
  a process, so if `server.py` ever imports `main.py`, only one config wins.
  Do not add a third `basicConfig` call reachable from either entry point.
- Do not use `print` in non-handler production code.
