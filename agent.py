# agent.py
from pathfinder import a_star_search

class Agent:
    def __init__(self, agent_id, start_pos):
        self.id = agent_id
        self.pos = start_pos
        self.target = None
        self.path = []
        self.state = "IDLE" 
        self.color = (255, 50, 50)
        self.timer = 0
        self.task_complete = False

    def set_target(self, target_pos, allowed_moves):
        self.target = target_pos
        # Initial search assumes map is empty (no dynamic obstacles yet)
        path = a_star_search(self.pos, self.target, allowed_moves)
        
        if path:
            self.path = path
            self.state = "MOVE"
            self.task_complete = False
        else:
            self.state = "IDLE"

    def reroute(self, blocked_pos, allowed_moves):
        """
        Called when the agent bumps into someone. 
        Recalculates path treating 'blocked_pos' as a wall.
        """
        # print(f"Agent {self.id}: Bumped! Rerouting to avoid {blocked_pos}...")
        
        # We pass the blocked position as a set of obstacles
        new_path = a_star_search(self.pos, self.target, allowed_moves, obstacles={blocked_pos})
        
        if new_path:
            self.path = new_path
            # print(f"Agent {self.id}: Found new path via side-step.")
        else:
            # No alternative path (e.g., deep in a single lane tunnel)
            # We keep the old path and just wait.
            pass

    def update(self):
        # (Keep your existing update logic exactly as is)
        if self.state == "MOVE":
            if self.path:
                if self.path[0] == self.pos:
                    self.path.pop(0)

                if self.path:
                    self.pos = self.path[0]
                else:
                    self.state = "LOADING"
                    self.timer = 20
                    # print(f"Agent {self.id}: Arrived. Starting work...")

        elif self.state == "LOADING":
            if self.timer > 0:
                self.timer -= 1
                self.color = (0, 255, 0)
            else:
                self.state = "IDLE"
                self.task_complete = True
                self.color = (255, 50, 50)

        elif self.state == "WAIT":
            self.color = (255, 255, 0)