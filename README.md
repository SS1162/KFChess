# KFChess — Kung-Fu Chess Engine

A real-time chess engine inspired by **Kung-Fu Chess**: there are no turns. Any piece can be moved at any time, and moves take time to complete — a piece travels across the board at a fixed speed, and the board only changes when it arrives.

The engine is a headless, deterministic simulator written in pure Python. It reads a board and a script of commands from standard input, runs them against a virtual clock, and prints the board on request.

## Features

- **Real-time movement** — a move takes `1000 ms` per cell of travel (Chebyshev distance).
- **All six piece types** — King, Queen, Rook, Bishop, Knight, Pawn, with path-blocking for sliding pieces.
- **Pawn rules** — forward step, diagonal capture, double step from the back rank, and promotion to Queen.
- **Mid-flight conflict resolution** — moves that become invalid while a piece is travelling are cancelled (destination taken, path blocked, piece captured before it left).
- **Game-over detection** — capturing a king ends the game; further moves are ignored.
- **Mouse-style input** — clicks are given in pixel coordinates and translated to board cells (`100 px` per cell).
- **Any board size** — rectangular boards of any dimension, validated on load.
- **Robust input handling** — malformed commands are logged and skipped; invalid boards produce a clear error code.

## Requirements

- Python 3.10+
- `pytest` (only for running the tests)

No third-party runtime dependencies.

## Usage

```bash
python main.py < input.txt
```

### Input format

```
Board:
bR . bK
. . .
wP . wK
Commands:
click 50 250
click 50 150
wait 1000
print board
```

**Board section** — one row per line, tokens separated by spaces:

| Token | Meaning |
|-------|---------|
| `.` | Empty square |
| `w` / `b` + `K Q R B N P` | White / black piece (e.g. `wK`, `bN`) |

White pawns move toward row 0 (top); black pawns move toward the last row.

**Commands section:**

| Command | Description |
|---------|-------------|
| `click <x> <y>` | Click at pixel `(x, y)`. The first click selects a piece; the second click on a target square starts the move. Clicking the same piece again deselects it; clicking another friendly piece switches the selection. |
| `wait <ms>` | Advance the virtual clock by `ms` milliseconds and land every piece that has arrived. |
| `print board` | Print the current board to stdout. |

Output for the example above:

```
bR . bK
wP . .
. . wK
```

### Errors

If the board is invalid, the program prints a single line and exits:

| Output | Cause |
|--------|-------|
| `ERROR EMPTY_BOARD` | No board rows |
| `ERROR ROW_WIDTH_MISMATCH` | Rows have different lengths |
| `ERROR UNKNOWN_TOKEN` | A token is not a valid piece or `.` |

Invalid commands are not fatal: they are skipped and logged to `kfchess.log`.

## How a move works

1. **Select** — `click` on a piece stores it as the current selection.
2. **Validate** — `click` on a target square asks the piece's move validator whether the move is legal, and checks that no other travelling piece is already headed there.
3. **Schedule** — the move is registered as *in flight* with an arrival time of `now + distance × 1000 ms`. The piece stays on its origin square until then.
4. **Arrive** — on `wait`, every move whose arrival time has passed lands, earliest first. On each landing the engine:
   - captures whatever is on the destination square,
   - promotes a pawn that reached the last row,
   - ends the game if a king was captured,
   - cancels in-flight moves that started from or were headed to that square,
   - cancels in-flight moves whose path is now blocked.

## Project structure

```
main.py                   Composition root: wires registries together and runs the input loop
parser.py                 TextBoardParser (input sections) and CommandParser (keyword → command)
validator.py              BoardValidator: board shape and token checks
commands.py               Immutable command objects: ClickCommand, WaitCommand, PrintBoardCommand
command_executor.py       CommandExecutor: command type → handler
handlers/
  click.py                Click parsing + selection / move-request logic
  wait.py                 Wait parsing + clock advance
  print_board.py          Print parsing + board output
game_state.py             GameState: clock, selection, in-flight moves, arrival resolution
board.py                  Board: grid storage and primitive mutations
movement.py               MoveContext, per-piece move rules, MoveValidator registry
game_status.py            GameStatus enum and GameOverRegistry
coordinate_translator.py  Pixel → board-cell conversion
models.py                 Value objects: Point, BoardPosition, Move
constants.py              Tunables: cell size, travel speed, pawn rules
exceptions.py             Board and command error hierarchy
tests/                    Unit tests (pytest)
```

## Architecture

The code is organised as a pipeline:

```
stdin ─► TextBoardParser ─► BoardValidator ─► Board / GameState
                │
                └─► CommandParser ─► Command ─► CommandExecutor ─► Handler ─► GameState
```

Key design decisions:

- **Registry pattern everywhere** — `CommandParser`, `CommandExecutor`, `MoveValidator` and `GameOverRegistry` all map a key to a function. Adding a new command, piece or win condition is a single `register(...)` call in `main.py`; existing classes do not change (Open/Closed Principle).
- **Composition root** — all wiring happens in `main.py`. Handlers receive their dependencies through the constructor (e.g. `ClickCommandHandler(move_validator)`), which keeps them easy to test.
- **Command objects** — parsing and execution are separated by small frozen dataclasses, so input syntax can change without touching game logic.
- **Virtual clock** — time only advances on `wait`. The simulation is fully deterministic and tests need no sleeping or mocking of time.
- **Single responsibility** — `Board` only stores tokens, `GameState` owns the timing rules, `movement.py` owns the geometry, and the handlers translate user intent into state changes.
- **Typed error hierarchy** — every board error carries an `error_code`; command errors derive from `ValueError` and are caught at the parser boundary.

## Running the tests

```bash
pip install pytest
python -m pytest
```

The suite contains 104 fast, isolated unit tests covering parsing, validation, movement rules, handlers and in-flight conflict resolution.
