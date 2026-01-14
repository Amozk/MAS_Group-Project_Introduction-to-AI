# train.py
import gymnasium as gym
from stable_baselines3 import PPO
from warehouse_env import WarehouseEnv
import os

# 1. Create the Environment
# We disable rendering during training to speed it up (render_mode=None)
env = WarehouseEnv(render_mode=None, num_agents=4)

# 2. Define the Model
# MlpPolicy = Multi-Layer Perceptron (Basic Neural Network)
model = PPO("MlpPolicy", env, verbose=1, learning_rate=0.0003, n_steps=2048)

print("---------------------------------------")
print("STARTING TRAINING... (This may take a while)")
print("The AI is exploring: FIFO vs Skipping Tasks")
print("---------------------------------------")

# 3. Train the Model
# total_timesteps=100000 is a short run. For good results, try 1,000,000+
model.learn(total_timesteps=100000)

# 4. Save the Model
models_dir = "models/PPO"
if not os.path.exists(models_dir):
    os.makedirs(models_dir)
    
model_path = f"{models_dir}/warehouse_opt_100k"
model.save(model_path)
print(f"Model saved to {model_path}")

# 5. Test the Trained Model (Visualizer)
print("Training complete. Switching to Visual Mode...")
env.close()

# Re-open with human rendering
env = WarehouseEnv(render_mode="human", num_agents=4)
obs, _ = env.reset()

running = True
while running:
    # Predict the best action using the trained model
    action, _states = model.predict(obs)
    
    # Take that action in the environment
    obs, reward, terminated, truncated, info = env.step(action)
    
    env.render()
    
    if terminated:
        obs, _ = env.reset()