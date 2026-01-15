# warehouse_env.py
import pygame
import random
import numpy as np
import gymnasium as gym
from gymnasium import spaces

from warehouse_map import build_map, build_sectors, WIDTH, HEIGHT, CELL_SIZE
from visualizer import draw_grid, draw_agent, draw_path
from agent import Agent

# AGENT COLORS:
AGENT_COLORS = [
    (255, 50, 50),   # Red
    (50, 50, 255),   # Blue
    (255, 165, 0),   # Orange
    (255, 0, 255)    # Magenta
]

class WarehouseEnv(gym.Env):
    metadata = {"render_modes": ["human", "rgb_array"], "render_fps": 10}

    def __init__(self, render_mode=None, num_agents=4, active_agents=None):
        super().__init__()
        
        # --- Map Setup ---
        self.grid, self.allowed_moves = build_map()
        self.sector_map = build_sectors(self.grid)
        self.shed_pos = (WIDTH // 2, HEIGHT - 2)
        self.shed_tiles = [
            (WIDTH // 2 - 1, HEIGHT - 2), 
            (WIDTH // 2, HEIGHT - 2)
        ]
        
        # --- Dimensions ---
        self.width = WIDTH
        self.height = HEIGHT
        self.cell_size = CELL_SIZE
        self.num_agents = num_agents

        self.active_agents = active_agents if active_agents is not None else num_agents
        
        # --- IMPROVEMENT 2: SMARTER EYES (Relative Coordinates) ---
        # 1. Agent Positions: [x, y] * num_agents
        # 2. Task Vectors: [dx, dy] relative to Shed * 3 tasks
        # Previous size was (num_agents * 2) + 3. 
        # New size is (num_agents * 2) + 6.
        obs_size = (num_agents * 2) + 6 
        
        # We allow negative values now (relative vectors can be negative)
        self.observation_space = spaces.Box(
            low=-max(WIDTH, HEIGHT), high=max(WIDTH, HEIGHT), shape=(obs_size,), dtype=np.float32
        )
        
        # Action Space stays the same (Pick Index 0, 1, or 2)
        self.action_space = spaces.Discrete(3)

        # --- Simulation State ---
        self.agents = []
        self.task_queue = []
        self.sector_occupancy = {}
        self.window = None
        self.clock = None
        self.render_mode = render_mode

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        
        # 1. Regenerate Tasks
        all_sector_locs = list(self.sector_map.keys())
        all_pallet_locs = [
            (x, y) for (x, y) in all_sector_locs 
            if self.grid[y][x] == "P" and (x, y) not in self.shed_tiles
        ]
        self.task_queue = [random.choice(all_pallet_locs) for _ in range(100)]
        
        # 2. Reset Agents
        self.agents = []
        spawn_points = [
            (2, self.height - 2), (self.width - 3, self.height - 2),
            (8, self.height - 2), (19, self.height - 2)
        ]
        
        for i in range(self.num_agents):
            # LOGIC: If agent index is >= active_agents, hide them!
            if i < self.active_agents:
                pos = spawn_points[i % len(spawn_points)]
                self.agents.append(Agent(i, pos))
            else:
                # Phantom Agents: Place them far off-screen so they don't block anyone
                # They exist for the 'Brain Shape' but do nothing.
                self.agents.append(Agent(i, (-100, -100))) 
            
        # 3. Initial Dispatch (Only for active agents)
        for agent in self.agents:
            if agent.pos[0] > -50: # Check if agent is on screen
                if self.task_queue:
                    target = self.task_queue.pop(0)
                    agent.set_target(target, self.allowed_moves)
                
        self.sector_occupancy = {}
        
        return self._get_obs(), {}

    def step(self, action):
        terminated = False
        truncated = False

        total_reward = 0
        total_reward -= 0.01 * self.num_agents

        # --- 0. WAKE UP LOGIC (For Interactive Mode) ---
        for agent in self.agents:
            if agent.state == "TERMINATED" and self.task_queue:
                agent.state = "IDLE"
                agent.task_complete = True 
        
        # --- 1. DISPATCHER LOGIC (Optimized) ---
        for agent in self.agents:
            if agent.pos[0] < -50: continue # Skip Phantoms
            
            # --- FIX: HIRE UNEMPLOYED AGENTS ---
            # Condition A: Agent finished a task (task_complete)
            # Condition B: Agent is sitting idle with no target (Unemployed / Initial State)
            is_unemployed = (agent.state == "IDLE" and agent.target is None)
            
            if agent.task_complete or is_unemployed:
                total_reward += 10.0 if agent.task_complete else 0 # Only reward finishing work
                
                # If agent finished a task (or is unemployed), go to Shed
                if agent.pos not in self.shed_tiles:
                    closest_shed = min(self.shed_tiles, key=lambda p: abs(p[0]-agent.pos[0]) + abs(p[1]-agent.pos[1]))
                    agent.set_target(closest_shed, self.allowed_moves)
                else:
                    # If at shed, get new task
                    if self.task_queue:
                        idx = action
                        if idx >= len(self.task_queue): idx = 0
                        next_task = self.task_queue.pop(idx)
                        agent.set_target(next_task, self.allowed_moves)
                    else:
                        agent.state = "TERMINATED"
                        agent.path = []
                
                agent.task_complete = False

        # --- 2. MOVEMENT LOOP (With Reward Shaping) ---
        for agent in self.agents:
            if agent.pos[0] < -50: continue # Skip Phantoms

            if agent.state == "TERMINATED":
                continue

            if agent.state == "LOADING":
                agent.update()
                continue
            
            # --- REWARD SHAPING ADDITION (START) ---
            # 1. Calculate Distance BEFORE Moving
            prev_dist = 0
            if agent.target:
                prev_dist = abs(agent.pos[0] - agent.target[0]) + abs(agent.pos[1] - agent.target[1])
            # ---------------------------------------

            # ASK THE AGENT: "Where do you want to go?"
            next_pos = agent.negotiate_move(self.allowed_moves, self.agents, self.shed_tiles)
            
            if next_pos:
                can_move = True
                
                # A. SAFETY NET: Physical Collision
                if next_pos not in self.shed_tiles:
                    for other in self.agents:
                        if other.id != agent.id and other.pos == next_pos:
                            can_move = False
                            break
                
                # B. SECTOR MANAGER
                curr_sec = self.sector_map.get(agent.pos)
                next_sec = self.sector_map.get(next_pos)
                
                if next_sec is not None and next_sec != curr_sec:
                    if next_pos not in self.shed_tiles: 
                        owner = self.sector_occupancy.get(next_sec)
                        if owner is not None and owner != agent.id:
                            can_move = False
                
                if can_move:
                    # Update Sector Manager
                    if curr_sec is not None and curr_sec != next_sec:
                        if self.sector_occupancy.get(curr_sec) == agent.id:
                            del self.sector_occupancy[curr_sec]
                    
                    if next_sec is not None:
                        if next_pos not in self.shed_tiles:
                            self.sector_occupancy[next_sec] = agent.id
                    
                    # Commit the move
                    agent.pos = next_pos
                
                agent.update()

            # --- REWARD SHAPING ADDITION (END) ---

            # C. Calculate Distance AFTER Moving & Apply Reward
            if agent.target:
                curr_dist = abs(agent.pos[0] - agent.target[0]) + abs(agent.pos[1] - agent.target[1])
                
                if curr_dist < prev_dist:
                    total_reward += 0.1  # Reward: Got closer!
                elif curr_dist > prev_dist:
                    total_reward -= 0.1  # Penalty: Moved away (or was forced to yield)
                
                # Note: If dist is same (waiting), the standard time penalty (-0.01) applies

        active_list = [a for a in self.agents if a.pos[0] > -50]
        if all(a.state == "TERMINATED" for a in active_list):
            terminated = True
            
        return self._get_obs(), total_reward, terminated, truncated, {}

    def _get_obs(self):
        # 1. Agent Positions (Absolute is fine, traffic awareness)
        agent_locs = np.array([a.pos for a in self.agents], dtype=np.float32).flatten()
        
        # 2. Task Vectors (Relative to Shed)
        # We want the Brain to know: "Task A is 10 steps Left (-10), Task B is 2 steps Right (+2)"
        # Since dispatching happens at the Shed, we measure from self.shed_pos.
        task_vectors = []
        shed_x, shed_y = self.shed_pos
        
        for i in range(3): # Look at next 3 tasks
            if i < len(self.task_queue):
                t_pos = self.task_queue[i]
                
                # VECTOR MATH: Target - Current
                dx = t_pos[0] - shed_x
                dy = t_pos[1] - shed_y
                
                task_vectors.extend([dx, dy])
            else:
                # No task available? Give (0,0) - Effectively "Right here" (or done)
                task_vectors.extend([0, 0])
        
        # Combine: [Ag1_x, Ag1_y, ... , Task1_dx, Task1_dy, Task2_dx...]
        return np.concatenate([agent_locs, np.array(task_vectors, dtype=np.float32)])

    def render(self):
        if self.render_mode == "human":
            if self.window is None:
                pygame.init()
                pygame.font.init() # Init font for debug text
                self.window = pygame.display.set_mode((self.width * self.cell_size, self.height * self.cell_size))
                pygame.display.set_caption("Warehouse MAS Debugger")
                self.clock = pygame.time.Clock()
                self.font = pygame.font.SysFont("Arial", 12) # Small font
            
            self.window.fill((30, 30, 30)) # Dark background
            draw_grid(self.window, self.grid, self.allowed_moves)

            # 1. Draw Targets (White Boxes)
            pending_locations = set(self.task_queue)
            for (tx, ty) in pending_locations:
                cx = tx * self.cell_size + self.cell_size // 2
                cy = ty * self.cell_size + self.cell_size // 2
                pygame.draw.rect(self.window, (255, 255, 255), (cx - 4, cy - 4, 10, 10))

            if self.task_queue:
                nx, ny = self.task_queue[0]
                cx = nx * self.cell_size + self.cell_size // 2
                cy = ny * self.cell_size + self.cell_size // 2
                pygame.draw.circle(self.window, (0, 255, 255), (cx, cy), 6, width=2)

            # 2. Draw Agents & Debug Info
            for agent in self.agents:
                if agent.pos[0] < -50: continue # Skip Phantoms
                
                # A. Draw Path Line (Trace)
                if agent.path:
                    points = [(p[0] * self.cell_size + self.cell_size//2, p[1] * self.cell_size + self.cell_size//2) for p in [agent.pos] + agent.path]
                    if len(points) > 1:
                        pygame.draw.lines(self.window, AGENT_COLORS[agent.id], False, points, 2)

                # B. Draw Target Line (Direct line to goal)
                if agent.target:
                    start = (agent.pos[0] * self.cell_size + self.cell_size//2, agent.pos[1] * self.cell_size + self.cell_size//2)
                    end = (agent.target[0] * self.cell_size + self.cell_size//2, agent.target[1] * self.cell_size + self.cell_size//2)
                    # Thin dotted line color based on state
                    line_col = (100, 100, 100) 
                    pygame.draw.line(self.window, line_col, start, end, 1)

                # C. Draw Agent Body
                color = AGENT_COLORS[agent.id]
                if agent.state == "WAIT": color = (255, 255, 0)
                elif agent.state == "LOADING": color = (0, 255, 0)
                elif agent.state == "TERMINATED": color = (100, 100, 100)
                
                cx = agent.pos[0] * self.cell_size + self.cell_size // 2
                cy = agent.pos[1] * self.cell_size + self.cell_size // 2
                pygame.draw.circle(self.window, color, (cx, cy), self.cell_size // 2 - 2)
                
                # --- DEBUG FEATURE 1: PATIENCE BAR ---
                # Draw a small bar above agent head
                if hasattr(agent, 'patience') and hasattr(agent, 'max_patience'):
                    bar_width = 20
                    bar_height = 4
                    fill_pct = agent.patience / agent.max_patience
                    bar_x = cx - bar_width // 2
                    bar_y = cy - 20
                    
                    # Background (Red)
                    pygame.draw.rect(self.window, (255, 0, 0), (bar_x, bar_y, bar_width, bar_height))
                    # Foreground (Green)
                    pygame.draw.rect(self.window, (0, 255, 0), (bar_x, bar_y, bar_width * fill_pct, bar_height))

                # --- DEBUG FEATURE 2: STATE ID ---
                # Draw letter "W" (Wait), "L" (Load), "M" (Move)
                state_char = agent.state[0]
                text = self.font.render(state_char, True, (0, 0, 0))
                self.window.blit(text, (cx - 3, cy - 8))

            pygame.display.flip()
            self.clock.tick(self.metadata["render_fps"])

    def close(self):
        if self.window is not None:
            pygame.quit()