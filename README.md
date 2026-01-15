# Warehouse Multi-Agent System (MAS) Project

## Overview

This project implements a Multi-Agent System (MAS) for warehouse management using reinforcement learning. Agents collaborate to optimize task allocation, pathfinding, and resource utilization in a simulated warehouse environment. The system uses PPO (Proximal Policy Optimization) for training agents through curriculum learning.

## Features

- **Multi-Agent Coordination**: Agents work together to handle tasks efficiently.
- **Reinforcement Learning**: Trained using Stable Baselines3 with PPO algorithm.
- **Curriculum Learning**: Two-stage training process (Solo → Team).
- **Visualization**: Real-time simulation with Pygame.
- **Interactive Debugging**: Manual task assignment and agent inspection.
- **Dataset Generation**: Tools to generate warehouse datasets from the simulation.

## Prerequisites

- Python 3.11.x
- Required libraries: gymnasium, stable-baselines3, pygame, numpy

## Installation

1. Clone or download the project repository.
2. Install the required dependencies:

   ```bash
   pip install gymnasium stable-baselines3 pygame numpy
   ```

## Project Structure

- `agent.py`: Defines the agent behavior and decision-making.
- `warehouse_env.py`: The warehouse environment simulation.
- `warehouse_map.py`: Map generation and management.
- `train.py`: Training script for the AI agents.
- `test.py`: Script to run the live simulation.
- `debug_runner.py`: Interactive debugging tool.
- `generate_dataset.py`: Dataset generation utility.
- `visualizer.py`: Visualization components.
- `pathfinder.py`: Pathfinding algorithms.
- `models/PPO/`: Directory for saved trained models.
- `warehouse_dataset.csv`: Generated dataset from simulation.

## Operation Modes

### 1. Training the AI (Curriculum Learning):
Run the training script to teach the agents from scratch. This runs a Two-Stage process (Solo -> Team).

```bash
python train.py
```

Output: Saves the trained model to models/PPO/warehouse_final_mas.

### 2. Live Simulation (Visual Demonstration):
Run the visualizer to watch the trained agents working.

```bash
python test.py
```

Interaction: The window will open showing the warehouse operation.

### 3. Interactive Debugging:
Run the debugger to manually stress-test the system.

```bash
python debug_runner.py
```

- `Left Click`: Force-assign a priority task to a specific tile.
- `Right Click`: Inspect an agent's internal state (Patience, Path, Reasoning).