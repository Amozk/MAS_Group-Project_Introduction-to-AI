# agent.py
import random
from pathfinder import a_star_search

class Agent:
    def __init__(self, agent_id, start_pos):
        self.id = agent_id
        self.pos = start_pos
        self.target = None
        self.path = []
        self.state = "IDLE" 
        self.color = (255, 50, 50)
        
        # --- TRUE MAS ATTRIBUTES ---
        self.max_patience = random.randint(5, 20) 
        self.patience = self.max_patience
        self.stuck_count = 0       # "Planning": Tracks if I'm totally deadlocked
        
        self.timer = 0
        self.task_complete = False

    def set_target(self, target_pos, allowed_moves):
        self.target = target_pos
        # --- SEARCHING ---
        path = a_star_search(self.pos, self.target, allowed_moves)
        
        if path:
            self.path = path
            self.state = "MOVE"
            self.task_complete = False
            self.patience = self.max_patience # Reset patience on new task
        else:
            self.state = "IDLE"

    def update(self):
        # Standard State Machine
        if self.state == "LOADING":
            if self.timer > 0:
                self.timer -= 1
                self.color = (0, 255, 0)
            else:
                self.state = "IDLE"
                self.task_complete = True
                self.color = (255, 50, 50)
        
        elif self.state == "WAIT":
            self.color = (255, 255, 0) # Visual feedback for "Reasoning"

    def negotiate_move(self, allowed_moves, other_agents, shed_tiles):
        """
        The Core MAS Brain: Reasoning & Planning & Yielding
        """
        # --- FIX 1: CLEAN THE PATH FIRST ---
        while self.path and self.path[0] == self.pos:
            self.path.pop(0)

        # --- FIX 2: RESUME MISSION / STOP INFINITE LOADING ---
        if not self.path:
            # We are at the target
            if self.pos == self.target:
                if self.state != "LOADING" and not self.task_complete:
                    self.state = "LOADING"
                    self.timer = 20
                return None
            else:
                # --- NEW FIX: Don't pathfind if we don't have a target! ---
                if self.target is None:
                    self.state = "IDLE"
                    return None
                # ----------------------------------------------------------

                # We are lost (maybe just yielded?) -> Re-calculate path to target
                path = a_star_search(self.pos, self.target, allowed_moves)
                if path:
                    self.path = path
                    self.state = "MOVE"
                else:
                    self.state = "IDLE"
                    return None

        next_pos = self.path[0]
        
        # 1. OBSERVATION: Who is in my way?
        blocker = None
        
        # Only look for blockers if we are NOT entering the shed
        if next_pos not in shed_tiles:
            for other in other_agents:
                if other.id != self.id and other.pos == next_pos:
                    blocker = other
                    break
        
        # 2. REASONING: Conflict Resolution
        if blocker:
            # Case A: Blocker is working (LOADING). Replan immediately.
            if blocker.state == "LOADING":
                self.force_replan(allowed_moves, obstacle=next_pos)
                return self.pos 
            
            # Case B: Blocker has same target (Queueing).
            elif blocker.target == self.target:
                 self.state = "WAIT"
                 return self.pos
            
            # Case C: Random Traffic. Use Patience.
            else:
                if self.patience > 0:
                    self.patience -= 1
                    self.state = "WAIT"
                    return self.pos
                else:
                    # STEP 1: PLAN (Try to go around)
                    success = self.force_replan(allowed_moves, obstacle=next_pos)
                    
                    if not success:
                        # STEP 2: YIELD (Planning failed? I must move aside.)
                        self.yield_position(allowed_moves, other_agents, shed_tiles)
                    
                    return self.pos

        # 3. EXECUTION
        self.max_patience = random.randint(5, 20) 
        self.patience = self.max_patience 
        self.state = "MOVE"
        
        # We already popped self.pos at the top, so just return next_pos
        return next_pos

    def force_replan(self, allowed_moves, obstacle):
        """
        PLANNING: The agent actively creates a new plan 
        treating the blockage as a permanent wall.
        Returns: True if successful, False if no path found.
        """
        new_path = a_star_search(
            self.pos, 
            self.target, 
            allowed_moves, 
            obstacles={obstacle} # Treat the person as a wall
        )
        
        if new_path:
            self.path = new_path
            self.patience = self.max_patience # Reset patience
            self.state = "MOVE"
            return True
        else:
            self.state = "WAIT"
            return False

    def yield_position(self, allowed_moves, other_agents, shed_tiles):
        """
        FALLBACK REASONING: 
        Find ANY valid neighbor that isn't the blockage and step there.
        """
        valid_moves = allowed_moves.get(self.pos, set())
        
        # Gather occupied positions to avoid yielding into someone else
        occupied = {a.pos for a in other_agents if a.id != self.id}
        
        candidates = []
        for move in valid_moves:
            dx, dy = move
            neighbor = (self.pos[0] + dx, self.pos[1] + dy)
            
            # Don't step into the thing we are blocked by (current path target)
            if self.path and neighbor == self.path[0]: continue
            
            # Don't step on other people
            if neighbor in occupied and neighbor not in shed_tiles: continue
            
            candidates.append(neighbor)
            
        if candidates:
            # Pick a random spot to step aside
            random.shuffle(candidates)
            yield_tile = candidates[0]
            
            # Overwrite path to just go there. 
            self.path = [yield_tile]
            self.patience = self.max_patience # Reset patience
            self.state = "MOVE"