# Valid board tokens: color-prefixed pieces (wK, bQ, …) and '.' for an empty square.
ALLOWED_TOKENS = frozenset(
    {'.'}
    | {color + piece for color in 'wb' for piece in 'KQRBNP'}
)

CELL_SIZE = 100          # pixels per board cell (width and height)
TIME_PER_CELL_MS  = 1000 # milliseconds of travel time per cell of distance moved

PAWN_DOUBLE_STEP_ROWS = 1   # rows from the edge that qualify as the pawn's start row (1 = back rank)
PAWN_PROMOTION_PIECE  = 'Q' # piece a pawn becomes upon reaching the last row

JUMP_DURATION_MS = 1000  # milliseconds a piece stays airborne after a jump
