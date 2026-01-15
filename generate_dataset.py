# generate_dataset.py
import csv
import numpy as np
from warehouse_env import WarehouseEnv
from stable_baselines3 import PPO

# --- CONFIGURATION ---
MODEL_PATH = "models/PPO/warehouse_final_mas" # Path to your trained model
OUTPUT_FILE = "warehouse_dataset.csv"
STEPS_TO_LOG = 1000 # How many timesteps to record

# 1. Setup Environment & Model
env = WarehouseEnv(render_mode=None, num_agents=4, active_agents=4)
model = PPO.load(MODEL_PATH, env=env)
obs, _ = env.reset()

print(f"Starting Data Collection...")
print(f"Output Target: {OUTPUT_FILE}")

# 2. Open File and Write Headers
# We use the 'with' block to safely handle file opening/closing
with open(OUTPUT_FILE, mode='w', newline='') as file:
    writer = csv.writer(file)
    
    # DEFINE THE 12 COLUMNS (Features)
    headers = [
        "Step_ID",
        "Agent_ID",
        "Agent_Pos_X",
        "Agent_Pos_Y",
        "Task_1_Vector_X",
        "Task_1_Vector_Y",
        "Task_2_Vector_X",
        "Task_2_Vector_Y",
        "Task_3_Vector_X",
        "Task_3_Vector_Y",
        "Current_Patience",
        "Is_Loading",
        "Action_Chosen",   # (Dispatch Decision)
        "Reward_Received"  # (Global Feedback)
    ]
    writer.writerow(headers)

    # 3. Simulation Loop
    for step_num in range(STEPS_TO_LOG):
        # Predict action from the Brain (PPO)
        action, _ = model.predict(obs)
        
        # Step the environment
        obs, reward, terminated, truncated, info = env.step(action)
        
        # 4. Extract Data Per Agent
        # We assume the 'Action' applies to the agent currently at the shed, 
        # but for the dataset, we can log the global action for context.
        
        # Calculate Task Vectors (Shared global info)
        # (Re-using logic from _get_obs to be accurate)
        shed_x, shed_y = env.shed_pos
        task_vectors = []
        for i in range(3):
            if i < len(env.task_queue):
                t_pos = env.task_queue[i]
                dx = t_pos[0] - shed_x
                dy = t_pos[1] - shed_y
                task_vectors.append((dx, dy))
            else:
                task_vectors.append((0, 0))
        
        # Write one row PER AGENT
        for agent in env.agents:
            # Feature Extraction
            row = [
                step_num,                   # Time
                agent.id,                   # ID
                agent.pos[0],               # Feat 1: Pos X
                agent.pos[1],               # Feat 2: Pos Y
                task_vectors[0][0],         # Feat 3: Task 1 dx
                task_vectors[0][1],         # Feat 4: Task 1 dy
                task_vectors[1][0],         # Feat 5: Task 2 dx
                task_vectors[1][1],         # Feat 6: Task 2 dy
                task_vectors[2][0],         # Feat 7: Task 3 dx
                task_vectors[2][1],         # Feat 8: Task 3 dy
                agent.patience,             # Feat 9: Patience
                1 if agent.state == "LOADING" else 0, # Feat 10: Is Loading?
                action,                     # Feat 11: The Dispatcher's Action
                round(reward, 4)            # Feat 12: Reward (Rounded)
            ]
            
            writer.writerow(row)

        if step_num % 100 == 0:
            print(f"Logged {step_num}/{STEPS_TO_LOG} steps...")

        if terminated:
            obs, _ = env.reset()

print("---------------------------------------")
print("Data Collection Complete!")
print(f"File generated: {OUTPUT_FILE}")
print("You can now open this file in Excel or use it for your report.")
print("---------------------------------------")