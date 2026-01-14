# warehouse_map.py

# Latest Checkpoint: Might need some semantic corrections such as BIDIR usage

WIDTH, HEIGHT = 28, 18
CELL_SIZE = 30  # pixels

WALL = "#"
BIDIR = "="
ONEWAY = "."    # Not used in current map
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

    # Outer paths Corners
    grid[1][1] = BIDIR               # Top-left
    grid[1][WIDTH-2] = BIDIR         # Top-right
    grid[HEIGHT-2][1] = BIDIR        # Bottom-left
    grid[HEIGHT-2][WIDTH-2] = BIDIR  # Bottom-right

    allowed_moves[(1, 1)] = {RIGHT, DOWN}
    allowed_moves[(WIDTH-2, 1)] = {LEFT, DOWN}
    allowed_moves[(1, HEIGHT-2)] = {RIGHT, UP}
    allowed_moves[(WIDTH-2, HEIGHT-2)] = {LEFT, UP}

    # Inner paths
    # Horizontal aisles
    for y in range(4, HEIGHT-4, 4):
        for x in range(2, WIDTH-2):
            grid[y][x] = JUNCTION
            grid[y+1][x] = JUNCTION
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

    # Pallet access points
    for y in range(2, HEIGHT-2, 4):
        for x in range(2, WIDTH-2):
            grid[y][x] = PALLET
            grid[y+1][x] = PALLET
            allowed_moves[(x, y)] = {UP}
            allowed_moves[(x, y+1)] = {DOWN}

    # Vertical aisles
    for y in range(4, HEIGHT-2):
            grid[y][WIDTH // 2 - 1] = JUNCTION
            allowed_moves[(WIDTH // 2 - 1, y)] = {UP, DOWN, RIGHT}
            grid[y][WIDTH // 2] = JUNCTION
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

    # Loading shed
    grid[HEIGHT-2][WIDTH // 2 - 1], grid[HEIGHT-2][WIDTH // 2] = SHED, SHED
    allowed_moves[(WIDTH // 2 - 1, HEIGHT-2)] = {LEFT, RIGHT, UP}
    allowed_moves[(WIDTH // 2, HEIGHT-2)] = {LEFT, RIGHT, UP}

    return grid, allowed_moves

def build_sectors(grid):
    """
    Assign a sector ID to each pallet access point.
    Splits rows into Left and Right sectors.
    
    - Top rows (Sector 0, 1): Include x=13, x=14 because they are 'P'.
    - Other rows (Sector 2+): Exclude x=13, x=14 because they are '+'.
    """
    sector_map = {}
    sector_id = 0
    visited_rows = set()
    
    rows = len(grid)
    cols = len(grid[0])
    mid_point = cols // 2  # 14
    
    # We scan specifically from column 2 to 26 (width-2)
    # The ranges below are key:
    # Left:  2 to 14 (indices 2..13)
    # Right: 14 to 26 (indices 14..25)

    for y in range(rows):
        if y in visited_rows:
            continue

        # Check if this row is part of a Pallet group
        if any(grid[y][x] == "P" for x in range(cols)):
            
            # Identify the pair of rows (e.g., 2 and 3)
            row_pair = [r for r in [y, y + 1] if r < rows]
            
            # --- LEFT SECTOR ---
            left_found = False
            for r in row_pair:
                # Scan up to mid_point (14) so we include index 13
                for x in range(2, mid_point): 
                    if grid[r][x] == "P":
                        sector_map[(x, r)] = sector_id
                        left_found = True
            
            if left_found:
                sector_id += 1

            # --- RIGHT SECTOR ---
            right_found = False
            for r in row_pair:
                # Scan starting from mid_point (14) so we include index 14
                for x in range(mid_point, cols - 2): 
                    if grid[r][x] == "P":
                        sector_map[(x, r)] = sector_id
                        right_found = True

            if right_found:
                sector_id += 1

            visited_rows.update(row_pair)

    return sector_map
