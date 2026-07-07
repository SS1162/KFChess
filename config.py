# Valid board tokens: color-prefixed pieces (wK, bQ, …) and '.' for an empty square.
ALLOWED_TOKENS = frozenset(
    {'.'}
    | {color + piece for color in 'wb' for piece in 'KQRBNP'}
)
