import nengo

import pacman_world
reload(pacman_world)

mymap="""
#######
#  S  #
#     #
#  #  #
#     #
#  E  #
#######
"""

model = nengo.Network()
with model:
    pacman = pacman_world.PacmanWorld(mymap)
    
    manual_control = nengo.Node([0, 0])
    nengo.Connection(manual_control, pacman.move)
    
    
    food = nengo.Ensemble(n_neurons=100, dimensions=2)
    
    nengo.Connection(pacman.detect_food, food)
    
    nengo.Connection(food[0], pacman.move[1])
    
    obstacles = nengo.Ensemble(n_neurons=300, dimensions=3, radius=4)
    nengo.Connection(pacman.obstacles[[1, 2, 3]], obstacles)
    
    def avoid(x):
        return 1*(x[2] - x[0])
    nengo.Connection(obstacles, pacman.move[1], function=avoid)
    
    def ahead(x):
        return 1*(x[1] - 0.5)
    nengo.Connection(obstacles, pacman.move[0], function=ahead)
    
    enemy = nengo.Ensemble(n_neurons=100, dimensions=2)
    nengo.Connection(pacman.detect_enemy, enemy)
    
    def run_away(x):
        return -x[1], -x[0]
    nengo.Connection(enemy, pacman.move, function=run_away, transform=2)
        

