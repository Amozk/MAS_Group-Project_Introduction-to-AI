# main.py
import pygame
from warehouse_map import build_map, WIDTH, HEIGHT, CELL_SIZE
from visualizer import draw_grid

pygame.init()

screen = pygame.display.set_mode(
    (WIDTH * CELL_SIZE, HEIGHT * CELL_SIZE)
)
pygame.display.set_caption("Warehouse Directional Grid")

clock = pygame.time.Clock()
grid, allowed_moves = build_map()

running = True
while running:
    clock.tick(30)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    screen.fill((0,0,0))
    draw_grid(screen, grid, allowed_moves)
    pygame.display.flip()

pygame.quit()
