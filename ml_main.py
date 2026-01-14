# main.py (Final - RL Ready)
from warehouse_env import WarehouseEnv

# Initialize the Gym Environment
env = WarehouseEnv(render_mode="human", num_agents=4)
obs, info = env.reset()

running = True
total_reward = 0

print("Starting Simulation via Gym Environment...")

while running:
    # 1. Action Step
    # Currently we send Action 0 (Placeholder) because heuristics handle logic inside env.step()
    # In the future, your RL model will predict this action.
    action = 0 
    
    # 2. Environment Step
    obs, reward, terminated, truncated, info = env.step(action)
    total_reward += reward
    
    # 3. Render
    env.render()
    
    if terminated:
        print(f"Episode Finished! Total Reward: {total_reward}")
        # Automatically restart
        obs, info = env.reset()
        total_reward = 0

env.close()