import pygame
import sys
from stable_baselines3 import PPO
from warehouse_env import WarehouseEnv
# We import CELL_SIZE from the map (Source of Truth) to calculate clicks.
# This keeps visualizer.py clean.
from warehouse_map import CELL_SIZE 

def run_interactive_simulation():
    # 1. Load the Environment
    # render_mode="human" tells the Env to initialize Pygame window
    env = WarehouseEnv(render_mode="human", num_agents=4)

    # 2. Load the Model
    model_path = "models/PPO/warehouse_final_mas" 
    model = None

    try:
        model = PPO.load(model_path)
        print(f"Successfully loaded model from {model_path}")
    except FileNotFoundError:
        print(f"WARNING: Could not find model at {model_path}")
        print("Running in RANDOM mode (Agents will pick random tasks).")

    # 3. Simulation Setup
    obs, info = env.reset()

    pygame.init()
    env.render()
    
    print("-------------------------------------------------")
    print("INTERACTIVE MODE ACTIVE")
    print("1. Simulation running...")
    print("2. LEFT CLICK on any Pallet Rack (Orange Tiles) to assign a task.")
    print("3. Close the window to exit.")
    print("-------------------------------------------------")

    running = True

    while running:
        # --- A. EVENT LOOP (The Controller Logic) ---
        # We handle inputs here in test.py so visualizer.py stays pure.
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1: # Left Click
                    # 1. Get Mouse Pixel Coordinates
                    mx, my = pygame.mouse.get_pos()
                    
                    # 2. Convert to Grid Coordinates
                    grid_x = mx // CELL_SIZE
                    grid_y = my // CELL_SIZE
                    clicked_pos = (grid_x, grid_y)
                    
                    # 3. Check Validity (Is it a known sector/pallet location?)
                    # We access the environment's map directly to validate.
                    if clicked_pos in env.sector_map:
                        print(f"[USER] Priority Task assigned at {clicked_pos}")
                        
                        # Inject task at FRONT of queue (High Priority)
                        env.task_queue.insert(0, clicked_pos)
                        
                        # 4. Wake Up Logic
                        # If agents are sleeping (Terminated), wake them up to do this new job.
                        for agent in env.agents:
                            if agent.state == "TERMINATED":
                                agent.state = "IDLE"
                                agent.task_complete = True 
                    else:
                        print(f"[USER] Clicked {clicked_pos} - Not a valid target.")

        # --- B. AI PREDICTION ---
        if model:
            action, _states = model.predict(obs, deterministic=True)
        else:
            action = env.action_space.sample()

        # --- C. SIMULATION STEP ---
        obs, reward, terminated, truncated, info = env.step(action)
        
        # --- D. RENDER ---
        # This calls env.render(), which internally uses visualizer.py functions.
        env.render()
        
        # Note: We keep the loop running even if terminated, so you can click to add more tasks.

    env.close()
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    run_interactive_simulation()