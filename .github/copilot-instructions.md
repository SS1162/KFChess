# KFChess — Coding Agent Instructions

## Project overview

KFChess is a real-time chess engine that processes a text-based board + command
stream from stdin and mutates game state in response to click, jump, wait, and
print commands. There is no GUI; the engine is exercised entirely through tests
and stdin piping.

## Tech stack

- **Language**: Python 3 (no third-party runtime dependencies)
- **Test runner**: `pytest` (only dependency; no `requirements.txt` — install
  with `pip install pytest` if missing)
- **No build step**: run tests directly with `pytest` from the repo root

## Repository layout

```
/                        ← project root (also sys.path root for imports)
├── main.py              ← entry point; wires all registries and runs the loop
├── board.py             ← Board dataclass (grid mutation)
├── game_state.py        ← mutable engine state (clock, in-flight, airborne, status)
├── game_status.py       ← GameStatus enum + GameOverRegistry
├── movement.py          ← per-piece move validators + MoveValidator registry
├── coordinate_translator.py  ← pixel → BoardPosition conversion
├── parser.py            ← TextBoardParser (stdin) + CommandParser (registry)
├── command_executor.py  ← CommandExecutor registry
├── commands.py          ← frozen command dataclasses (Click/Jump/Wait/Print)
├── models.py            ← frozen value objects (Point, BoardPosition, Move)
├── constants.py         ← CELL_SIZE, TIME_PER_CELL_MS, JUMP_DURATION_MS, …
├── exceptions.py        ← BoardError / CommandError hierarchies
├── validator.py         ← BoardValidator (structural grid checks)
├── conftest.py          ← adds repo root to sys.path (required for test imports)
├── handlers/            ← one module per command: click, jump, wait, print_board
│   └── *.py             ← each exports parse_<cmd> and handle_<cmd>
└── tests/               ← pytest test files (test_*.py)
```

## Architecture: registry pattern

Every extensible subsystem uses the same registry pattern — **never modify the
registry class itself to add a new entry**:

| Registry class    | Key type     | Registered in  |
|-------------------|--------------|----------------|
| `CommandParser`   | keyword str  | `main.py`      |
| `CommandExecutor` | command type | `main.py`      |
| `MoveValidator`   | piece letter | `main.py`      |
| `GameOverRegistry`| token str    | `game_status.py` |

To add a new command: create a `commands.py` dataclass, add `parse_*` /
`handle_*` in `handlers/`, and register both in `main.py`.

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
- Logging goes to `kfchess.log` (WARNING level); do not use `print` in
  non-handler production code.
