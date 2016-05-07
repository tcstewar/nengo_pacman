import random

import nengo

import cellular
import continuous

class Cell(cellular.Cell):
    food = False
    pacman_start = False
    enemy_start = False
    def color(self):
        if self.wall:
            return 'black'
        if self.food:
            return 'yellow'
        return None
    def load(self, char):
        if char == '#':
            self.wall = True
        elif char == 'S':
            self.pacman_start = True
        elif char == 'E':
            self.enemy_start = True
        else:
            self.food = True




class GridNode(nengo.Node):
    def __init__(self, world, dt=0.001):
        def svg(t):
            last_t = getattr(svg, '_nengo_html_t_', None)
            if t <= last_t:
                last_t = None
            if last_t is None or t >= last_t + dt:
                svg._nengo_html_ = self.generate_svg(world)
                svg._nengo_html_t_ = t
        super(GridNode, self).__init__(svg)

    def generate_svg(self, world):
        cells = []
        for i in range(world.width):
            for j in range(world.height):
                cell = world.get_cell(i, j)
                color = cell.color
                if callable(color):
                    color = color()
                if color is not None:
                    cells.append('<rect x=%d y=%d width=1 height=1 style="fill:%s"/>' %
                        (i, j, color))

        agents = []
        for agent in world.agents:
            direction = agent.dir * 360.0 / world.directions
            color = getattr(agent, 'color', 'blue')
            if callable(color):
                color = color()
            agent = ('<polygon points="0.25,0.25 -0.25,0.25 0,-0.5"'
                     ' style="fill:%s" transform="translate(%f,%f) rotate(%f)"/>'
                     % (color, agent.x+0.5, agent.y+0.5, direction))
            agents.append(agent)

        svg = '''<svg width="100%%" height="100%%" viewbox="0 0 %d %d">
            %s
            %s
            </svg>''' % (world.width, world.height,
                         ''.join(cells), ''.join(agents))

        return svg

class PacmanWorld(nengo.Network):
    def __init__(self, worldmap,
                 pacman_speed=20, pacman_rotate=10,
                 ghost_speed=5, ghost_rotate=5,
                 **kwargs):
        super(PacmanWorld, self).__init__(**kwargs)
        self.world = cellular.World(Cell, map=worldmap, directions=4)

        self.pacman = continuous.Body()
        self.pacman.score = 0

        self.ghost_rotate = ghost_rotate
        self.ghost_speed = ghost_speed

        starting = list(self.world.find_cells(lambda cell: cell.pacman_start))
        if len(starting) == 0:
            starting = list(self.world.find_cells(lambda cell: cell.food))
        cell = random.choice(starting)

        total = len(list(self.world.find_cells(lambda cell: cell.food)))

        self.world.add(self.pacman, cell=cell, dir=3)

        self.enemies = []
        for cell in self.world.find_cells(lambda cell: cell.enemy_start):
            ghost = continuous.Body()
            ghost.color = 'red'
            self.world.add(ghost, cell=cell, dir=1)
            self.enemies.append(ghost)

        self.completion_time = None

        with self:
            self.environment = GridNode(self.world)

            def move(t, x):
                speed, rotation = x
                dt = 0.001
                self.pacman.turn(rotation * dt * pacman_rotate)
                self.pacman.go_forward(speed * dt * pacman_speed)

                if self.pacman.cell.food:
                    self.pacman.score += 1
                    self.pacman.cell.food = False
                    if self.completion_time is None and self.pacman.score == total:
                        self.completion_time = t

                for ghost in self.enemies:
                    self.update_ghost(ghost)

            self.move = nengo.Node(move, size_in=2)

            def score(t):
                html = '<h1>%d / %d</h1>' % (self.pacman.score, total)
                if self.completion_time is not None:
                    html += 'Completed in<br/>%1.3f seconds' % self.completion_time
                else:
                    html += '%1.3f seconds' % t
                html = '<center>%s</center>' % html
                score._nengo_html_ = html
            self.score = nengo.Node(score)

    def update_ghost(self, ghost):
        dt = 0.001

        target_dir = ghost.get_direction_to(self.pacman)

        theta = ghost.dir - target_dir
        while theta > 2: theta -= 4
        while theta < -2: theta += 4

        ghost.turn(-theta * dt * self.ghost_rotate)
        ghost.go_forward(self.ghost_speed * dt)

        if ghost.get_distance_to(self.pacman) < 0.5:
            self.reset()

    def reset(self):
        self.pacman.score = 0

        for row in self.world.grid:
            for cell in row:
                if not (cell.wall or cell.pacman_start or cell.enemy_start):
                    cell.food = True

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
















