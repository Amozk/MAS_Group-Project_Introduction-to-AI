# warehouse_map.py

WIDTH, HEIGHT = 26, 15
CELL_SIZE = 30  # pixels

WALL = "#"
BIDIR = "="
ONEWAY = "."
SHED = "S"
PALLET = "P"

UP = (0, -1)
DOWN = (0, 1)
LEFT = (-1, 0)
RIGHT = (1, 0)

def build_map():
    grid = [[WALL for _ in range(WIDTH)] for _ in range(HEIGHT)]
    allowed_moves = {}

    # Outer boundary paths
    for x in range(1, WIDTH-1):
        grid[1][x] = BIDIR
        allowed_moves[(x, 1)] = {LEFT, RIGHT}

        grid[HEIGHT-2][x] = BIDIR
        allowed_moves[(x, HEIGHT-2)] = {LEFT, RIGHT}

    # Vertical aisles (bidirectional)
    for y in range(2, HEIGHT-2, 2):
        for x in range(2, WIDTH-2, 4):
            grid[y][x] = BIDIR
            allowed_moves[(x, y)] = {UP, DOWN}

    # Half-aisles (one-way)
    for y in range(3, HEIGHT-3, 2):
        for x in range(3, WIDTH-3, 4):
            grid[y][x] = ONEWAY
            allowed_moves[(x, y)] = {RIGHT}

    # Pallet access points
    for y in range(3, HEIGHT-3, 2):
        for x in range(4, WIDTH-3, 4):
            grid[y][x] = PALLET
            allowed_moves[(x, y)] = set()

    # Loading shed
    grid[1][1] = SHED
    allowed_moves[(1, 1)] = {RIGHT, DOWN}

    return grid, allowed_moves
