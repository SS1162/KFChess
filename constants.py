# Valid board tokens: color-prefixed pieces (wK, bQ, …) and '.' for an empty square.
ALLOWED_TOKENS = frozenset(
    {'.'}
    | {color + piece for color in 'wb' for piece in 'KQRBNP'}
)

CELL_SIZE = 100          # pixels per board cell (width and height)
TIME_PER_CELL_MS  = 1000 # milliseconds of travel time per cell of distance moved
