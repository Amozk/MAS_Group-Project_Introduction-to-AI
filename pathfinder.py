# pathfinder.py
import heapq

class PriorityQueue:
    def __init__(self):
        self.elements = []
    
    def empty(self):
        return len(self.elements) == 0
    
    def put(self, item, priority):
        heapq.heappush(self.elements, (priority, item))
    
    def get(self):
        return heapq.heappop(self.elements)[1]

def heuristic(a, b):
    # Manhattan distance
    (x1, y1) = a
    (x2, y2) = b
    return abs(x1 - x2) + abs(y1 - y2)

def a_star_search(start, goal, allowed_moves, obstacles=None):
    """
    Standard A* but accepts a set of 'obstacles' (coordinates) 
    that should be treated as walls for this specific search.
    """
    if obstacles is None:
        obstacles = set()

    frontier = PriorityQueue()
    frontier.put(start, 0)
    
    came_from = {}
    cost_so_far = {}
    
    came_from[start] = None
    cost_so_far[start] = 0
    
    while not frontier.empty():
        current = frontier.get()
        
        if current == goal:
            break
        
        # Get neighbors explicitly from the allowed_moves dictionary
        # If a tile isn't in allowed_moves, it's a wall.
        moves = allowed_moves.get(current, set())
        
        for move in moves:
            # Calculate neighbor coordinates
            dx, dy = move
            next_node = (current[0] + dx, current[1] + dy)
            
            # --- THE FIX: DYNAMIC OBSTACLE CHECK ---
            if next_node in obstacles:
                continue # Treat this tile as a wall
            # ---------------------------------------

            # Standard A* Logic
            if next_node not in allowed_moves:
                continue

            new_cost = cost_so_far[current] + 1
            if next_node not in cost_so_far or new_cost < cost_so_far[next_node]:
                cost_so_far[next_node] = new_cost
                priority = new_cost + heuristic(next_node, goal)
                frontier.put(next_node, priority)
                came_from[next_node] = current
                
    # Reconstruct path
    path = []
    if goal not in came_from:
        return [] # No path found
        
    curr = goal
    while curr != start:
        path.append(curr)
        curr = came_from[curr]
    path.append(start)
    path.reverse()
    
    return path