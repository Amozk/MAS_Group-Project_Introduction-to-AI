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
    for y in range(2, HEIGHT, 4):
        for x in range(2, WIDTH-2):
            grid[y][x] = JUNCTION
            grid[y+1][x] = JUNCTION
            allowed_moves[(x, y)] = {LEFT, RIGHT, UP, DOWN}
            allowed_moves[(x, y+1)] = {LEFT, RIGHT, UP, DOWN}

    # Bottom path adjacent to wall
    for x in range(2, WIDTH-2):
        grid[HEIGHT-2][x] = JUNCTION
        allowed_moves[(x, HEIGHT-2)] = {LEFT, RIGHT, UP}

    # Side junctions
    for y in range(2, HEIGHT-2, 4):
        grid[y][1] = JUNCTION
        grid[y+1][1] = JUNCTION
        grid[y][WIDTH-2] = JUNCTION
        grid[y+1][WIDTH-2] = JUNCTION
        allowed_moves[(1, y)] = {UP, DOWN, RIGHT}
        allowed_moves[(1, y+1)] = {UP, DOWN, RIGHT}
        allowed_moves[(WIDTH-2, y)] = {UP, DOWN, LEFT}
        allowed_moves[(WIDTH-2, y+1)] = {UP, DOWN, LEFT}

    # Pallet access points
    for y in range(0, HEIGHT-2, 4):
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
    for y in range(2, HEIGHT-2, 4):
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

    # Minor adjustment
    for x in range(0, WIDTH):
        grid[0][x] = WALL
        allowed_moves.pop((x, 0), None)

    return grid, allowed_moves

def build_sectors(grid):
    """
    Custom Sector Definition based on User Coordinates.
    - Row 1: Full width (meets in middle).
    - Row 2-4: Gap in middle (Cols 13, 14 free).
    """
    sector_map = {}
    sector_id = 0
    rows = len(grid)     # 18
    cols = len(grid[0])  # 28
    
    # Define your 4 specific "Aisle" groups (The walking paths)
    # Format: (y_start, y_end, x_left_end, x_right_start)
    # Note: Python ranges are exclusive at the end, so we add +1 to the end index.
    
    definitions = [
        # Row 1 (y=2 to 3): Left 2-13, Right 14-End
        {"y_range": (2, 4), "left_x": (2, 14), "right_x": (14, cols-2)},
        
        # Row 2 (y=6 to 7): Left 2-12, Right 15-End (Gap in middle)
        {"y_range": (6, 8), "left_x": (2, 13), "right_x": (15, cols-2)},
        
        # Row 3 (y=10 to 11): Left 2-12, Right 15-End (Gap in middle)
        {"y_range": (10, 12), "left_x": (2, 13), "right_x": (15, cols-2)},
        
        # Row 4 (y=14 to 15): Left 2-12, Right 15-End (Gap in middle)
        {"y_range": (14, 16), "left_x": (2, 13), "right_x": (15, cols-2)},
    ]

    for definition in definitions:
        y_start, y_end = definition["y_range"]
        
        # === LEFT SECTOR ===
        lx_start, lx_end = definition["left_x"]
        has_items = False
        
        # 1. Map the Aisle (Walking Path)
        for y in range(y_start, y_end):
            for x in range(lx_start, lx_end):
                sector_map[(x, y)] = sector_id
                has_items = True
                
                # 2. Map the Pallets ABOVE and BELOW this tile
                # Check y-1 (Top Pallet) and y+2 (Bottom Pallet relative to start)
                # We simply check neighbors vertically
                for check_y in [y-1, y+1]: # Check immediate neighbors
                    if 0 <= check_y < rows:
                        if grid[check_y][x] == "P":
                            sector_map[(x, check_y)] = sector_id

        if has_items:
            sector_id += 1

        # === RIGHT SECTOR ===
        rx_start, rx_end = definition["right_x"]
        has_items = False
        
        for y in range(y_start, y_end):
            for x in range(rx_start, rx_end):
                sector_map[(x, y)] = sector_id
                has_items = True
                
                # Map Pallets
                for check_y in [y-1, y+1]:
                    if 0 <= check_y < rows:
                        if grid[check_y][x] == "P":
                            sector_map[(x, check_y)] = sector_id

        if has_items:
            sector_id += 1

    return sector_map
