# warehouse_map.py

# Latest Checkpoint: Might need some semantic corrections such as BIDIR usage

WIDTH, HEIGHT = 28, 18
CELL_SIZE = 30  # pixels

WALL = "#"
BIDIR = "="
ONEWAY = "."
JUNCTION = "+"
SHED = "S"
PALLET = "P"

UP = (0, -1)
DOWN = (0, 1)
LEFT = (-1, 0)
RIGHT = (1, 0)

def build_map():
    grid = [[WALL for _ in range(WIDTH)] for _ in range(HEIGHT)]
    allowed_moves = {}

    # Outer paths
    for x in range(1, WIDTH-1, WIDTH-3):
        for y in range(1, HEIGHT-1):
            grid[y][x] = BIDIR
            allowed_moves[(x, y)] = {UP, DOWN}

    # Outer paths Corners as junctions
    grid[1][1] = JUNCTION               # Top-left
    grid[1][WIDTH-2] = JUNCTION         # Top-right
    grid[HEIGHT-2][1] = JUNCTION        # Bottom-left
    grid[HEIGHT-2][WIDTH-2] = JUNCTION  # Bottom-right

    allowed_moves[(1, 1)] = {RIGHT, DOWN}
    allowed_moves[(WIDTH-2, 1)] = {LEFT, DOWN}
    allowed_moves[(1, HEIGHT-2)] = {RIGHT, UP}
    allowed_moves[(WIDTH-2, HEIGHT-2)] = {LEFT, UP}

    # Inner paths
    # Horizontal aisles (bidirectional)
    for y in range(4, HEIGHT-4, 4):
        for x in range(2, WIDTH-2):
            grid[y][x] = BIDIR
            grid[y+1][x] = BIDIR
            allowed_moves[(x, y)] = {LEFT, RIGHT, UP, DOWN}
            allowed_moves[(x, y+1)] = {LEFT, RIGHT, UP, DOWN}

    # Pickup entry at top and bottom outer paths
    for x in range(2, WIDTH-2):
        grid[1][x] = JUNCTION
        grid[HEIGHT-2][x] = JUNCTION
        allowed_moves[(x, 1)] = {LEFT, RIGHT, DOWN}
        allowed_moves[(x, HEIGHT-2)] = {LEFT, RIGHT, UP}

    # Side junctions
    for y in range(4, HEIGHT-4, 4):
        grid[y][1] = JUNCTION
        grid[y+1][1] = JUNCTION
        grid[y][WIDTH-2] = JUNCTION
        grid[y+1][WIDTH-2] = JUNCTION
        allowed_moves[(1, y)] = {UP, DOWN, RIGHT}
        allowed_moves[(1, y+1)] = {UP, DOWN, RIGHT}
        allowed_moves[(WIDTH-2, y)] = {UP, DOWN, LEFT}
        allowed_moves[(WIDTH-2, y+1)] = {UP, DOWN, LEFT}

    # Pallet access points (one-way)
    for y in range(2, HEIGHT-2, 4):
        for x in range(2, WIDTH-2):
            grid[y][x] = PALLET
            grid[y+1][x] = PALLET
            allowed_moves[(x, y)] = set()
            allowed_moves[(x, y+1)] = set()

    # Vertical aisles (bidirectional)
    for y in range(4, HEIGHT-2):
            grid[y][WIDTH // 2 - 1] = BIDIR
            allowed_moves[(WIDTH // 2 - 1, y)] = {UP, DOWN, RIGHT}
            grid[y][WIDTH // 2] = BIDIR
            allowed_moves[(WIDTH // 2, y)] = {UP, DOWN, LEFT}

    # Middle Junctions
    for y in range(4, HEIGHT-4, 4):
        grid[y][WIDTH // 2 - 1] = JUNCTION
        grid[y+1][WIDTH // 2 - 1] = JUNCTION
        grid[y][WIDTH // 2] = JUNCTION
        grid[y+1][WIDTH // 2] = JUNCTION
        allowed_moves[(WIDTH // 2 - 1, y)] = {UP, DOWN, RIGHT, LEFT}
        allowed_moves[(WIDTH // 2 - 1, y+1)] = {UP, DOWN, RIGHT, LEFT}
        allowed_moves[(WIDTH // 2, y)] = {UP, DOWN, RIGHT, LEFT}
        allowed_moves[(WIDTH // 2, y+1)] = {UP, DOWN, RIGHT, LEFT}

    # Minor Adjustment
    grid[4][WIDTH // 2 - 1] = JUNCTION
    allowed_moves[(WIDTH // 2 - 1, 4)] = {DOWN, RIGHT, LEFT}
    grid[4][WIDTH // 2] = JUNCTION
    allowed_moves[(WIDTH // 2, 4)] = {DOWN, RIGHT, LEFT}

    # Loading shed
    grid[HEIGHT-2][WIDTH // 2 - 1], grid[HEIGHT-2][WIDTH // 2] = SHED, SHED
    allowed_moves[(WIDTH // 2 - 1, HEIGHT-2)] = {LEFT, RIGHT, UP}
    allowed_moves[(WIDTH // 2, HEIGHT-2)] = {LEFT, RIGHT, UP}

    return grid, allowed_moves
