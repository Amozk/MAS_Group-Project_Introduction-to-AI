# debug_runner.py
import pygame
import time
from warehouse_env import WarehouseEnv
from stable_baselines3 import PPO

# Load the trained model
models_dir = "models/PPO"
model_path = f"{models_dir}/warehouse_final_mas" # Or your latest model

print(f"Loading model from {model_path}...")

# Create env with all agents active for debugging
env = WarehouseEnv(render_mode="human", num_agents=4, active_agents=4)
model = PPO.load(model_path, env=env)

obs, _ = env.reset()
running = True

print("------------------------------------------------")
print("DEBUG MODE ACTIVE")
print(" [LEFT CLICK]  -> Force agent to move to this tile")
print(" [RIGHT CLICK] -> Inspect Agent (Brain Dump)")
print("------------------------------------------------")

while running:
    # 1. Predict Action
    action, _ = model.predict(obs)
    
    # 2. Step Environment
    obs, reward, terminated, truncated, info = env.step(action)
    env.render()
    
    # 3. Handle Human Input
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
            
        elif event.type == pygame.MOUSEBUTTONDOWN:
            # Get grid coordinates
            mx, my = pygame.mouse.get_pos()
            gx = mx // env.cell_size
            gy = my // env.cell_size
            clicked_pos = (gx, gy)
            
            # --- LEFT CLICK: Manual Task Assignment ---
            if event.button == 1: 
                print(f"\n[USER] Priority Task assigned at {clicked_pos}")
                # Force the first idle agent to go here
                found = False
                for agent in env.agents:
                    if agent.state != "LOADING":
                        agent.set_target(clicked_pos, env.allowed_moves)
                        agent.task_complete = False # Reset flag so they don't auto-shed
                        print(f" -> Re-routed Agent {agent.id} to {clicked_pos}")
                        found = True
                        break
                if not found:
                    print(" -> No available agents to take this task!")

            # --- RIGHT CLICK: Agent Inspector ---
            elif event.button == 3:
                print(f"\n[INSPECTOR] Checking tile {clicked_pos}...")
                found_agent = None
                for agent in env.agents:
                    if agent.pos == clicked_pos:
                        found_agent = agent
                        break
                
                if found_agent:
                    a = found_agent
                    print(f"=== AGENT {a.id} REPORT ===")
                    print(f" State:      {a.state}")
                    print(f" Patience:   {a.patience} / {a.max_patience}")
                    print(f" Target:     {a.target}")
                    print(f" Path Len:   {len(a.path)}")
                    print(f" Path Next:  {a.path[:3]}...") # Show next 3 steps
                    
                    # Logic Check: Why are you stuck?
                    if a.state == "WAIT":
                        print(" DIAGNOSIS: Agent is waiting.")
                        if len(a.path) > 0:
                            next_step = a.path[0]
                            print(f" -> Wants to go to {next_step}")
                            # Check who is there
                            blocker = None
                            for other in env.agents:
                                if other.pos == next_step and other.id != a.id:
                                    blocker = other
                            if blocker:
                                print(f" -> BLOCKED BY Agent {blocker.id} (State: {blocker.state})")
                            else:
                                print(f" -> Path is clear but agent is waiting. (Logic Bug?)")
                        else:
                            print(" -> No path available.")
                else:
                    print(" -> Empty tile.")

    if terminated:
        print("Episode finished. Resetting...")
        obs, _ = env.reset()

env.close()