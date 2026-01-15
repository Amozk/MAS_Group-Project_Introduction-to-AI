# train.py
import gymnasium as gym
from stable_baselines3 import PPO
from warehouse_env import WarehouseEnv
import os

models_dir = "models/PPO"
if not os.path.exists(models_dir):
    os.makedirs(models_dir)

# ==========================================
# STAGE 1: THE SOLO CURRICULUM (Easy Mode)
# ==========================================
print("---------------------------------------")
print("STAGE 1: Training Solo Agent (Learning Basics)...")
print("---------------------------------------")

# Initialize environment with 4 slots, but only 1 Active Agent
env_stage1 = WarehouseEnv(render_mode=None, num_agents=4, active_agents=1)

# Train a new model from scratch
model = PPO("MlpPolicy", env_stage1, verbose=1, learning_rate=0.0003, n_steps=2048)
model.learn(total_timesteps=50000) # Short run to learn basic fetching

# Save the "Pre-trained" brain
stage1_path = f"{models_dir}/warehouse_stage1_solo"
model.save(stage1_path)
print(f"Stage 1 Complete. Saved to {stage1_path}")

env_stage1.close() # Close to free up memory

# ==========================================
# STAGE 2: THE TEAM CURRICULUM (Hard Mode)
# ==========================================
print("---------------------------------------")
print("STAGE 2: Training Full Team (Learning Coordination)...")
print("---------------------------------------")

# Initialize environment with ALL 4 Agents active
env_stage2 = WarehouseEnv(render_mode=None, num_agents=4, active_agents=4)

# Load the brain from Stage 1
# This works because obs_size is identical (thanks to Phantom Agents)
model = PPO.load(stage1_path, env=env_stage2)

# Train for longer to adapt to traffic
model.learn(total_timesteps=150000) 

# Save the Final Model
final_path = f"{models_dir}/warehouse_final_mas"
model.save(final_path)
print(f"Stage 2 Complete. Final model saved to {final_path}")

# ==========================================
# VISUALIZATION
# ==========================================
print("Switching to Visual Mode...")
env_stage2.close()

env_test = WarehouseEnv(render_mode="human", num_agents=4, active_agents=4)
obs, _ = env_test.reset()

running = True
while running:
    action, _ = model.predict(obs)
    obs, reward, terminated, truncated, info = env_test.step(action)
    env_test.render()
    
    if terminated:
        obs, _ = env_test.reset()