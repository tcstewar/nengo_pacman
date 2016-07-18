import random
from random import randint
import numpy as np
import nengo
import cellular
import continuous
import body
from threading import Timer

# Global variables that contain information about the pacman and ghost
# The pacman and ghost classes extend the continuous body class
# Additonally, their parameters can be edited to change their state, color, size, etc.

# Add multiple Pacman or Ghosts (with controllers) w/out modifying code

#global ghost
#ghost = body.Player("ghost", "seeking", pacman.size, "red", 5, 5)

# The cell class encapsulates every "object" in the game (walls, food, enemies, pacman, etc.)
class Cell(cellular.Cell):

    # These are the inital states of the food, pacman start and enemy start booleans
    food = False
    pacman_start = False
    enemy_start = False
    state = None

    # The Color function sets the color of both the wall and food
    def color(self):
        if self.wall:
            return 'blue'
        if self.food:
            return 'white'
        return None

    # The load function runs through the mymap string passed in and initalizes starting positions for the pacman, enemy and food
    def load(self, char):

        if char == '#':
            self.wall = True
        elif char == 'S':
            self.pacman_start = True
        elif char == 'E':
            self.enemy_start = True
        elif char == ' ' and self.x%5==0 and self.y%5==0:
            self.food = True
            self.state = 'food'
        else:
            self.space = True

# GridNode sets up the pacman world for visualization
class GridNode(nengo.Node):
    def __init__(self, world, dt=0.001):

        # The initalizer sets up the html layout for display
        def svg(t):
            last_t = getattr(svg, '_nengo_html_t_', None)
            if t <= last_t:
                last_t = None
            if last_t is None or t >= last_t + dt:
                svg._nengo_html_ = self.generate_svg(world)
                svg._nengo_html_t_ = t
        super(GridNode, self).__init__(svg)

    # This function sets up an SVG (used to embed html code in the environment)
    def generate_svg(self, world):
        cells = []
        # Runs through every cell in the world (walls & food)
        listFood = list()
        for i in range(world.width):
            for j in range(world.height):
                cell = world.get_cell(i, j)
                color = cell.color
                if callable(color):
                    color = color()

                # If the cell is a wall, then set its appearance to a blue rectangle
                if cell.wall:
                    cells.append('<rect x=%d y=%d width=1 height=1 style="fill:%s"/>' %
                         (i, j, color))

                # If the cell is normal food, then set its appearance to a white circle
                if cell.food:
                    cells.append('<circle cx=%d cy=%d r=0.4 style="fill:%s"/>' %
                        (i, j, color))

        # Runs through every agent in the world (ghost & pacman)
        agents = []
        for agent in world.agents:

            # sets variables like agent direction, color and size
            direction = agent.dir * 360.0 / world.directions
            color = getattr(agent, 'color', 'yellow')
            if callable(color):
                color = color()
            s = agent.size * 2

            # Uses HTML rendering to setup the agents
            agent_poly = ('<image xlink:href="local/%s.png" x="%f" y="%f" '
                    ' width="%f" height="%f" transform="translate(%f,%f) rotate(%f)"/>'
                         % (agent.typeBody, -s/2, -s/2, s, s, agent.x+0.5, agent.y+0.5, direction - 90))

            agents.append(agent_poly)

        # Sets up the environment as a HTML SVG
        svg = '''<svg style="background: black" width="100%%" height="100%%" viewbox="0 0 %d %d">
            %s
            %s
            </svg>''' % (world.width, world.height,
                         ''.join(cells), ''.join(agents))
        return svg

# Main Pacman World class
class PacmanWorld(nengo.Network):

    def __init__(self, worldmap, pacman_speed = 70, pacman_rotate = 20,
                 ghost_speed = 5, ghost_rotate=5, dt=0.001,
                 **kwargs):

        # Initializes PacmanWorld using parameters from the global pacman and ghost variables
        super(PacmanWorld, self).__init__(**kwargs)
        self.world = cellular.World(Cell, map=worldmap, directions=4)
        self.pacman = body.Player("pacman", "eating", 2, "yellow", pacman_speed, pacman_rotate)
        self.ghost_rotate = ghost_rotate
        self.ghost_speed = ghost_speed
        self.last_t = None

        # Init for starting positions of the pacman and for food, etc.
        starting = list(self.world.find_cells(lambda cell: cell.pacman_start))
        if len(starting) == 0:
            starting = list(self.world.find_cells(lambda cell: cell.food))
        cell = random.choice(starting)
        total = len(list(self.world.find_cells(lambda cell: cell.food)))
        self.world.add(self.pacman, cell=cell, dir=3)

        # Adds a random amount of ghost enemies to the world
        self.enemies = []
        for cell in self.world.find_cells(lambda cell: cell.enemy_start):
            new = body.Player("ghost", "seeking", 0.37, "red", ghost_speed, ghost_rotate)
            self.world.add(new, cell=cell, dir=1)
            self.enemies.append(new)
        self.completion_time = None

        # Sets up environment for the GridNode (this includes the nodes for obstacles and food)
        with self:
            self.environment = GridNode(self.world, dt=dt)

            #Pacman's move function -- called every 0.001 second (set using dt)
            def move(t, x):
                if self.last_t is not None and t < self.last_t:
                    self.reset()
                self.last_t = t

                speed, rotation = x
                dt = 0.001

                # Pacman turns and moves forward based on obstacles and food availability
                self.pacman.turn(rotation * dt * pacman_rotate)
                self.pacman.go_forward(speed * dt * pacman_speed)

                # If pacman moves into a cell containing food...
                for n in self.pacman.cell.neighbours:
                    if n.food:
                        # Adds to the score and updates ghosts
                        self.pacman.score += 1
                        n.food = False
                        if self.completion_time is None and self.pacman.score == total:
                            self.completion_time = t

                for ghost in self.enemies:
                    self.update_ghost(ghost)

            self.move = nengo.Node(move, size_in=2)

            # The score is kept track of using an html rendering
            def score(t):
                html = '<h1>%d / %d</h1>' % (self.pacman.score, total)
                if self.completion_time is not None:
                    html += '<div style="background:yellow">Completed in<br/>%1.3f seconds</div>' % self.completion_time
                else:
                    html += '%1.3f seconds' % t
                html = '<center>%s</center>' % html
                score._nengo_html_ = html
            self.score = nengo.Node(score)

            # Sets up the node for the obstacles (this factors in angles and distances towards respective obstacles)
            def obstacles(t):
                angles = np.linspace(-0.5, 0.5, 3) + self.pacman.dir
                angles = angles % self.world.directions
                self.pacman.obstacle_distances = [self.pacman.detect(d, max_distance=4*2)[0] for d in angles]
                return self.pacman.obstacle_distances
            self.obstacles = nengo.Node(obstacles)

            # Sets up the node for the food (factors in amount of food in an area and its relative strength, distance, etc)
            def detect_food(t):
                x = 0
                y = 0

                # Runs through the total number of cells in the world and calculates strength and relative distance for each one
                for cell in self.world.find_cells(lambda cell:cell.food):
                    dir = self.pacman.get_direction_to(cell)
                    dist = self.pacman.get_distance_to(cell)
                    rel_dir = dir - self.pacman.dir
                    if dist > 5:
                        continue
                    if dist>=0.05:
                        strength = 1.0 / dist
                    else:
                        continue

                    dx = np.sin(rel_dir * np.pi / 2) * strength
                    dy = np.cos(rel_dir * np.pi / 2) * strength

                    x += dx
                    y += dy
                return x, y
            self.detect_food = nengo.Node(detect_food)

            # Sets up the node for the enemies (factors in number of enemies in an area and their relative strength, distance, etc.)
            def detect_enemy(t):
                x = 0
                y = 0

                # Runs through the total number of ghosts in the world and calculates strength and relative distance for each one
                for ghost in self.enemies:
                    dir = self.pacman.get_direction_to(ghost)
                    dist = self.pacman.get_distance_to(ghost)
                    rel_dir = dir - self.pacman.dir
                    strength = 1.0 / dist

                    dx = np.sin(rel_dir * np.pi / 2) * strength
                    dy = np.cos(rel_dir * np.pi / 2) * strength

                    x += dx
                    y += dy
                return x, y
            self.detect_enemy = nengo.Node(detect_enemy)

    # Updates the ghost's position every 0.001 second
    def update_ghost(self, ghost):
        dt = 0.001
        ghost.size=3

        # Updates the ghost's position based on angles and distance towards the obstacles, etc.
        angles = np.linspace(-1, 1, 5) + ghost.dir
        angles = angles % self.world.directions
        obstacle_distances = [ghost.detect(d, max_distance=4*2)[0] for d in angles]

        ghost.turn((obstacle_distances[1]-obstacle_distances[3])*-2 * dt * self.ghost_rotate)
        ghost.go_forward((obstacle_distances[2]-0.5)*2*self.ghost_speed * dt)

        target_dir = ghost.get_direction_to(self.pacman)

        # Factors in target distance and calls the turn and go_forward functions in that direction

        # If the ghost is in a seeking condition, then it is turning towards the pacman and going forward
        if(ghost.state == "seeking"):
            theta = ghost.dir - target_dir
            while theta > 2: theta -= 4
            while theta < -2: theta += 4
            ghost.turn(-theta * dt * self.ghost_rotate)
            ghost.go_forward(self.ghost_speed * dt)
            if ghost.get_distance_to(self.pacman) < 2:
                self.reset()

        # If the ghost is in a running condition, then it is turning away from the pacman and going forward
        elif(ghost.state == "running"):
            if ghost.get_distance_to(self.pacman) < 1:
                ghost.state = "seeking"
                ghost.cell = random.choice(starting)
            theta = ghost.dir - target_dir
            while theta > 2: theta -= 4
            while theta < -2: theta += 4
            ghost.turn(360-( -theta * dt * self.ghost_rotate))
            ghost.go_forward(self.ghost_speed * dt)

    # Resets the pacman's position after it loses
    def reset(self):
        self.pacman.score = 0
        self.completion_time = None

        # Runs through the rows in the world and reinializes cells
        for row in self.world.grid:
            for cell in row:
                if not (cell.wall or cell.pacman_start or cell.enemy_start) and (cell.state == "food"):
                    cell.food = True

        # reinializes the starting position of the pacman
        starting = list(self.world.find_cells(lambda cell: cell.pacman_start))
        if len(starting) == 0:
            starting = list(self.world.find_cells(lambda cell: cell.food))
        self.pacman.cell = random.choice(starting)
        self.pacman.x = self.pacman.cell.x
        self.pacman.y = self.pacman.cell.y
        self.pacman.dir = 3

        for i, cell in enumerate(self.world.find_cells(lambda cell: cell.enemy_start)):
            self.enemies[i].cell = cell
            self.enemies[i].dir = 1
            self.enemies[i].x = cell.x
            self.enemies[i].y = cell.y
