# warehouse_env.py
import pygame
import random
import numpy as np
import gymnasium as gym
from gymnasium import spaces

from warehouse_map import build_map, build_sectors, WIDTH, HEIGHT, CELL_SIZE
from visualizer import draw_grid, draw_agent
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

    def __init__(self, render_mode=None, num_agents=4):
        super().__init__()
        
        # --- Map Setup ---
        self.grid, self.allowed_moves = build_map()
        self.sector_map = build_sectors(self.grid)
        self.shed_pos = (WIDTH // 2, HEIGHT - 2)
        
        # --- Dimensions ---
        self.width = WIDTH
        self.height = HEIGHT
        self.cell_size = CELL_SIZE
        self.num_agents = num_agents
        
        # --- RL Spaces (Definitions) ---
        # Observation: For simplicity, let's just observe Agent Positions for now
        # Shape: [Num_Agents, 2] -> [[x1,y1], [x2,y2]...]
        self.observation_space = spaces.Box(
            low=0, high=max(WIDTH, HEIGHT), shape=(num_agents, 2), dtype=np.float32
        )
        
        # Action: A placeholder. 
        # 0 = Default (Heuristic), 1 = Force Wait, 2 = Force Reroute (Example)
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
        all_pallet_locs = list(self.sector_map.keys())
        self.task_queue = [random.choice(all_pallet_locs) for _ in range(100)]
        
        # 2. Reset Agents
        self.agents = []
        spawn_points = [
            (2, self.height - 2), (self.width - 3, self.height - 2),
            (8, self.height - 2), (19, self.height - 2)
        ]
        
        # Handle case if num_agents > spawn_points
        for i in range(self.num_agents):
            pos = spawn_points[i % len(spawn_points)]
            self.agents.append(Agent(i, pos))
            
        # 3. Initial Dispatch
        for agent in self.agents:
            if self.task_queue:
                target = self.task_queue.pop(0)
                agent.set_target(target, self.allowed_moves)
                
        self.sector_occupancy = {}
        
        return self._get_obs(), {}

    def step(self, action):
        total_reward = 0
        terminated = False
        truncated = False
        
        total_reward -= 0.01 * self.num_agents

        # --- 1. DISPATCHER LOGIC (Keep as is) ---
        for agent in self.agents:
            if agent.task_complete:
                total_reward += 10.0 
                if agent.pos != self.shed_pos:
                    agent.set_target(self.shed_pos, self.allowed_moves)
                else:
                    if self.task_queue:
                        idx = action
                        if idx >= len(self.task_queue): idx = 0
                        next_task = self.task_queue.pop(idx)
                        agent.set_target(next_task, self.allowed_moves)
                    else:
                        agent.state = "TERMINATED"
                        agent.path = []
                agent.task_complete = False

        # --- 2. MOVEMENT LOOP ---
        for agent in self.agents:
            if agent.state == "WAIT": total_reward -= 0.5
            if agent.state == "LOADING":
                agent.update()
                continue
            if not agent.path: continue

            next_step_idx = 0
            if len(agent.path) > 1 and agent.path[0] == agent.pos:
                next_step_idx = 1
            
            if next_step_idx < len(agent.path):
                next_pos = agent.path[next_step_idx]
                curr_sec = self.sector_map.get(agent.pos)
                next_sec = self.sector_map.get(next_pos)
                
                can_move = True
                
                # CHECK A: Sector Manager
                if next_sec is not None and next_sec != curr_sec:
                    owner = self.sector_occupancy.get(next_sec)
                    if owner is not None and owner != agent.id:
                        can_move = False
                        agent.state = "WAIT"
                
                # CHECK B: Physical Collision + REROUTE FIX
                if can_move:
                    for other in self.agents:
                        if other.id != agent.id and other.pos == next_pos:
                            can_move = False
                            agent.state = "WAIT"
                            
                            # --- THE FIX: COIN FLIP ---
                            # 50% chance to be "Optimistic" (Try to go around)
                            # 50% chance to be "Pessimistic" (Just wait and hope they move)
                            if random.random() < 0.5:
                                # "Excuse me, coming through!"
                                agent.reroute(next_pos, self.allowed_moves)
                            else:
                                # "I'll just wait here."
                                # We do NOT reroute, keeping the original path.
                                pass
                            
                            break

                # --- CHECK C: LANE LOCKING (Expanded for Side Aisles) ---
                if can_move:
                    # Fix: Include Side Lanes (1, WIDTH-2) AND Center Lanes
                    critical_lanes = [1, self.width - 2, self.width // 2 - 1, self.width // 2]
                    
                    if agent.pos[0] not in critical_lanes and next_pos[0] in critical_lanes:
                        target_lane_x = next_pos[0]
                        for other in self.agents:
                            if other.id != agent.id:
                                if other.pos[0] == target_lane_x:
                                    can_move = False
                                    agent.state = "WAIT"
                                    break
                
                # EXECUTE MOVE
                if can_move:
                    if agent.state == "WAIT": agent.state = "MOVE"
                    if curr_sec is not None and curr_sec != next_sec:
                        if self.sector_occupancy.get(curr_sec) == agent.id:
                            del self.sector_occupancy[curr_sec]
                    if next_sec is not None:
                        self.sector_occupancy[next_sec] = agent.id
                    agent.update()

        if all(a.state == "TERMINATED" for a in self.agents):
            terminated = True
            
        return self._get_obs(), total_reward, terminated, truncated, {}

    def _get_obs(self):
        # Return simple coordinate list as observation
        obs = np.array([a.pos for a in self.agents], dtype=np.float32)
        return obs

    def render(self):
        if self.render_mode == "human":
            if self.window is None:
                pygame.init()
                self.window = pygame.display.set_mode((self.width * self.cell_size, self.height * self.cell_size))
                pygame.display.set_caption("Warehouse RL Environment")
                self.clock = pygame.time.Clock()
            
            self.window.fill((0, 0, 0))
            draw_grid(self.window, self.grid, self.allowed_moves)

            # --- NEW: DRAW PATHS FIRST ---
            for agent in self.agents:
                # Pick a color based on ID (Red vs Blueish)
                # We make it slightly dimmer or distinct from the agent body
                base_color = AGENT_COLORS[agent.id]
                
                # If waiting, maybe show path in Yellow?
                if agent.state == "WAIT":
                    base_color = (200, 200, 50)
                
                # Draw the trail
                from visualizer import draw_path # Import locally or at top
                draw_path(self.window, agent.path, base_color)
            
            for agent in self.agents:
                color = AGENT_COLORS[agent.id]
                if agent.state == "WAIT": color = (255, 255, 0)
                elif agent.state == "LOADING": color = (0, 255, 0)
                elif agent.state == "TERMINATED": color = (100, 100, 100)
                draw_agent(self.window, agent.pos[0], agent.pos[1], color)
                
            # Draw Sector Locks
            for pos, sid in self.sector_map.items():
                if sid in self.sector_occupancy:
                    px, py = pos[0] * self.cell_size + 5, pos[1] * self.cell_size + 5
                    pygame.draw.rect(self.window, (255, 0, 0), (px, py, 5, 5))

            pygame.display.flip()
            self.clock.tick(self.metadata["render_fps"])

    def close(self):
        if self.window is not None:
            pygame.quit()