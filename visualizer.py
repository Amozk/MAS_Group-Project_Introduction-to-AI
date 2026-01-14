# visualizer.py
import pygame
from warehouse_map import CELL_SIZE, UP, DOWN, LEFT, RIGHT

COLORS = {
    "#": (40, 40, 40),      # wall
    "=": (200, 200, 200),  # bidirectional aisle
    ".": (180, 180, 255),  # one-way aisle
    "+": (255, 255, 150),  # junction
    "S": (100, 255, 100),  # shed
    "P": (255, 180, 100),  # pallet
}

def draw_arrow(screen, cx, cy, direction):
    x, y = cx, cy
    if direction == UP:
        pygame.draw.polygon(screen, (0,0,0), [(x,y-6),(x-4,y+4),(x+4,y+4)])
    elif direction == DOWN:
        pygame.draw.polygon(screen, (0,0,0), [(x,y+6),(x-4,y-4),(x+4,y-4)])
    elif direction == LEFT:
        pygame.draw.polygon(screen, (0,0,0), [(x-6,y),(x+4,y-4),(x+4,y+4)])
    elif direction == RIGHT:
        pygame.draw.polygon(screen, (0,0,0), [(x+6,y),(x-4,y-4),(x-4,y+4)])

def draw_grid(screen, grid, allowed_moves):
    for y, row in enumerate(grid):
        for x, cell in enumerate(row):
            rect = pygame.Rect(
                x * CELL_SIZE,
                y * CELL_SIZE,
                CELL_SIZE,
                CELL_SIZE
            )
            pygame.draw.rect(screen, COLORS[cell], rect)
            pygame.draw.rect(screen, (100,100,100), rect, 1)

            # Draw arrows
            if (x, y) in allowed_moves:
                cx = x * CELL_SIZE + CELL_SIZE // 2
                cy = y * CELL_SIZE + CELL_SIZE // 2
                for move in allowed_moves[(x, y)]:
                    draw_arrow(screen, cx, cy, move)

def draw_agent(screen, x, y, color=(255, 50, 50)):
    cx = x * CELL_SIZE + CELL_SIZE // 2
    cy = y * CELL_SIZE + CELL_SIZE // 2
    pygame.draw.circle(screen, color, (cx, cy), CELL_SIZE // 3)

def draw_path(screen, path, color):
    """
    Draws a visual trail for the agent's planned path.
    """
    if not path or len(path) < 2:
        return

    # Create a list of pixel coordinates for the center of each tile
    pixel_points = []
    for (gx, gy) in path:
        cx = gx * CELL_SIZE + CELL_SIZE // 2
        cy = gy * CELL_SIZE + CELL_SIZE // 2
        pixel_points.append((cx, cy))

    # Draw lines connecting the points
    # width=2 makes it a thin, unobtrusive line
    pygame.draw.lines(screen, color, False, pixel_points, width=2)
    
    # Optional: Draw tiny dots at each step to see discrete tiles
    for (cx, cy) in pixel_points:
        pygame.draw.circle(screen, color, (cx, cy), 3)