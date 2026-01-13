# main.py (Step E)

import pygame
from warehouse_map import build_map, WIDTH, HEIGHT, CELL_SIZE, UP, DOWN, LEFT, RIGHT
from visualizer import draw_grid, draw_agent

pygame.init()

screen = pygame.display.set_mode(
    (WIDTH * CELL_SIZE, HEIGHT * CELL_SIZE)
)
pygame.display.set_caption("Warehouse Grid – Arrow Legality Test")

clock = pygame.time.Clock()
grid, allowed_moves = build_map()

agent_x, agent_y = WIDTH // 2, HEIGHT -2
agent_color = (255, 50, 50)
flash_timer = 0

DIR_KEYS = {
    pygame.K_UP: UP,
    pygame.K_DOWN: DOWN,
    pygame.K_LEFT: LEFT,
    pygame.K_RIGHT: RIGHT
}

running = True
while running:
    clock.tick(30)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.KEYDOWN and event.key in DIR_KEYS:
            dx, dy = DIR_KEYS[event.key]

            if (agent_x, agent_y) in allowed_moves and (dx, dy) in allowed_moves[(agent_x, agent_y)]:
                nx = agent_x + dx
                ny = agent_y + dy

                if 0 <= nx < WIDTH and 0 <= ny < HEIGHT:
                    agent_x, agent_y = nx, ny
            else:
                # Illegal move → flash red
                flash_timer = 10

    # Handle flashing
    if flash_timer > 0:
        agent_color = (255, 0, 0)
        flash_timer -= 1
    else:
        agent_color = (255, 50, 50)

    screen.fill((0,0,0))
    draw_grid(screen, grid, allowed_moves)
    draw_agent(screen, agent_x, agent_y, agent_color)
    pygame.display.flip()

pygame.quit()