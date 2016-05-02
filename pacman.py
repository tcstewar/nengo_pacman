import nengo
import numpy as np    

# requires CCMSuite https://github.com/tcstewar/ccmsuite/
import ccm.lib.grid
import ccm.lib.continuous
import ui

mymap="""
#######
#     #
# # # #
# # # #
# # # #
#     #
#######
"""

class Cell(ccm.lib.grid.Cell):
    def color(self):
        if self.wall:
            return 'black'
        if self.food:
            return 'yellow'
        return None
    def load(self, char):
        if char == '#':
            self.wall = True
        self.food = True

world = ccm.lib.grid.World(Cell, map=mymap, directions=4)

body = ccm.lib.continuous.Body()
world.add(body, x=1, y=2, dir=2)
body.score = 0


model = nengo.Network(seed=2)
with model:
    def move(t, x):
        speed, rotation = x
        dt = 0.001
        max_speed = 20.0
        max_rotate = 10.0
        body.turn(rotation * dt * max_rotate)
        body.go_forward(speed * dt * max_speed)
        
        if body.cell.food:
            body.score += 1
            body.cell.food = False
    movement = nengo.Node(move, size_in=2)

    env = ui.GridNode(world, dt=0.005)

    def detect(t):
        angles = (np.linspace(-0.5, 0.5, 3) + body.dir ) % world.directions
        return [body.detect(d, max_distance=4)[0] for d in angles]
    stim_radar = nengo.Node(detect)

    radar = nengo.Ensemble(n_neurons=50, dimensions=3, radius=4, seed=2)
    nengo.Connection(stim_radar, radar)



    def position_func(t):
        return (body.x / world.width * 2 - 1, 
                1 - body.y/world.height * 2, 
                body.dir / world.directions)
    position = nengo.Node(position_func)
    
    state = nengo.Ensemble(100, 3)

    nengo.Connection(position, state, synapse=None)
    
    control = nengo.Node([0,0])
    move = nengo.Ensemble(100, 2)
    nengo.Connection(control, move)
    nengo.Connection(move, movement)
    
    
