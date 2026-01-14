# test.py
import gymnasium as gym
from stable_baselines3 import PPO
from warehouse_env import WarehouseEnv

# 1. Load the Environment (Visual Mode)
env = WarehouseEnv(render_mode="human", num_agents=4)

# 2. Load the Trained Model
# Make sure this path matches where train.py saved it!
model_path = "models/PPO/warehouse_opt_100k" 

try:
    model = PPO.load(model_path)
    print(f"Successfully loaded model from {model_path}")
except FileNotFoundError:
    print(f"Error: Could not find model at {model_path}")
    print("Did you run train.py fully?")
    exit()

# 3. Run the Simulation Loop
obs, info = env.reset()
running = True
total_reward = 0

print("Running Simulation... Press Close on window to stop.")

while running:
    # Ask the AI: "Given this observation (positions), what is the best action?"
    # deterministic=True means "Pick the absolute best action," no randomness.
    action, _states = model.predict(obs, deterministic=True)
    
    # Execute the action
    obs, reward, terminated, truncated, info = env.step(action)
    total_reward += reward
    
    # Render the graphics
    env.render()
    
    if terminated:
        print(f"Episode Finished! Total Score: {total_reward:.2f}")
        obs, info = env.reset()
        total_reward = 0

env.close()