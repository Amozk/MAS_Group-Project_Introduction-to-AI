# main.py (Step E)

import pygame
from warehouse_map import build_map, build_sectors, WIDTH, HEIGHT, CELL_SIZE, UP, DOWN, LEFT, RIGHT
from visualizer import draw_grid, draw_agent
from agent import Agent
from pathfinder import a_star_search
import random

pygame.init()

screen = pygame.display.set_mode(
    (WIDTH * CELL_SIZE, HEIGHT * CELL_SIZE)
)
pygame.display.set_caption("Warehouse Grid – Arrow Legality Test")

clock = pygame.time.Clock()
grid, allowed_moves = build_map()
sector_map = build_sectors(grid)

all_pallet_locs = list(sector_map.keys())
task_queue = [random.choice(all_pallet_locs) for _ in range(50)]

agents = [
    Agent(0, (2, HEIGHT - 2)),          # Far Left
    Agent(1, (WIDTH - 3, HEIGHT - 2)),  # Far Right
    Agent(2, (8, HEIGHT - 2)),          # Mid Left
    Agent(3, (19, HEIGHT - 2))          # Mid Right
]
agent_color = (255, 50, 50)
flash_timer = 0

for agent in agents:
    if task_queue:
        target = task_queue.pop(0)
        agent.set_target(target, allowed_moves)

sector_occupancy = {}

running = True
while running:
    clock.tick(10) 

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # --- PHASE 3: SIMPLE TASK MANAGER ---
    # --- PHASE 4: DISPATCHER (NCS Rule Implemented) ---
    shed_pos = (WIDTH // 2, HEIGHT - 2)

    for agent in agents:
        if agent.task_complete:
            # Case A: Agent just finished LOADING -> Go to Shed
            if agent.pos != shed_pos:
                print(f"Agent {agent.id}: Loaded! Returning to Shed.")
                agent.set_target(shed_pos, allowed_moves)
            
            # Case B: Agent just finished UNLOADING -> Needs new task
            else:
                if task_queue:
                    
                    # --- NCS LOGIC STARTS HERE ---
                    
                    # 1. Identify "Busy" Sectors
                    # A sector is busy if someone is INSIDE it or DRIVING to it
                    busy_sectors = set(sector_occupancy.keys())
                    for other_a in agents:
                        if other_a.id != agent.id and other_a.target:
                            # If another agent has a target, mark that sector as busy
                            # (We use .get because target might be the Shed, which has no sector)
                            target_sec = sector_map.get(other_a.target)
                            if target_sec is not None:
                                busy_sectors.add(target_sec)
                    
                    # 2. Search Queue for a "Free" Sector Task
                    selected_index = -1
                    for i, task_pos in enumerate(task_queue):
                        task_sector = sector_map.get(task_pos)
                        
                        # NCS Rule: Choose route with no common sector
                        if task_sector not in busy_sectors:
                            selected_index = i
                            print(f"DISPATCHER: NCS applied! Agent {agent.id} skips to task in free Sector {task_sector}.")
                            break
                    
                    # 3. Select the Task
                    if selected_index != -1:
                        # Found a conflict-free task
                        next_task = task_queue.pop(selected_index)
                    else:
                        # Fallback: All relevant sectors are busy. Take the first one.
                        next_task = task_queue.pop(0)
                        print(f"DISPATCHER: All sectors busy. Agent {agent.id} taking queue head (Sector {sector_map.get(next_task)}).")

                    # --- NCS LOGIC ENDS HERE ---

                    print(f"Agent {agent.id}: Assigned to {next_task}. Tasks left: {len(task_queue)}")
                    agent.set_target(next_task, allowed_moves)
                
                else:
                    print(f"Agent {agent.id}: No more tasks. Shift over.")
                    agent.state = "TERMINATED"
                    agent.path = []
            
            agent.task_complete = False

        # 2. Handle 'Working' State (LOADING)
        # If loading, we don't need traffic control. Just tick the timer.
        if agent.state == "LOADING":
            agent.update()
            continue

        # 3. Handle 'Movement' State (Traffic Control)
        # If no path, we are IDLE or TERMINATED, so skip
        if not agent.path:
            continue

        # --- SECTOR MANAGER LOGIC ---
        
        for agent in agents:
            # Skip if waiting for a task or working
            if not agent.path or agent.state == "LOADING":
                if agent.state == "LOADING": agent.update() # Keep timer ticking
                continue

            # 1. Determine Next Step
            next_step_index = 0
            if len(agent.path) > 1 and agent.path[0] == agent.pos:
                next_step_index = 1
            
            if next_step_index >= len(agent.path):
                continue
                
            next_pos = agent.path[next_step_index]
            
            # --- COLLISION CHECKS ---
            can_move = True
            
            # CHECK A: Sector Manager (High-Level Rules)
            curr_sec = sector_map.get(agent.pos)
            next_sec = sector_map.get(next_pos)
            
            if next_sec is not None and next_sec != curr_sec:
                owner = sector_occupancy.get(next_sec)
                if owner is not None and owner != agent.id:
                    can_move = False
                    # Debug: print(f"Agent {agent.id} wait: Sector Locked")

            # CHECK B: Physical Collision (Low-Level Bumper) <--- NEW!
            # Scan all other agents to see if anyone is standing on 'next_pos'
            if can_move: # Only check if sector didn't already block us
                for other_agent in agents:
                    if other_agent.id != agent.id:
                        if other_agent.pos == next_pos:
                            can_move = False
                            # Debug: print(f"Agent {agent.id} wait: Path blocked by Agent {other_agent.id}")
                            break

            # Execute Move
            if can_move:
                if agent.state == "WAIT":
                    agent.state = "MOVE"

                # Update Sector Ownership
                if curr_sec is not None and curr_sec != next_sec:
                    if sector_occupancy.get(curr_sec) == agent.id:
                        del sector_occupancy[curr_sec]
                        print(f"UNLOCKED: Sector {curr_sec} is now free.")
                
                if next_sec is not None:
                    sector_occupancy[next_sec] = agent.id
                
                agent.update()

    # --- DRAWING ---
    screen.fill((0,0,0))
    draw_grid(screen, grid, allowed_moves)
    
    for agent in agents:
        color = (255, 50, 50) if agent.id == 0 else (50, 50, 255)
        if agent.state == "WAIT":
            color = (255, 255, 0)
        elif agent.state == "LOADING": # Visual confirmation of work
            color = (0, 255, 0)
        elif agent.state == "TERMINATED":
            color = (100, 100, 100)
            
        draw_agent(screen, agent.pos[0], agent.pos[1], color)

    # Visualize Locked Sectors
    for pos, sector_id in sector_map.items():
        if sector_id in sector_occupancy:
             px = pos[0] * CELL_SIZE + 5
             py = pos[1] * CELL_SIZE + 5
             pygame.draw.rect(screen, (255, 0, 0), (px, py, 5, 5))

    pygame.display.flip()

pygame.quit()