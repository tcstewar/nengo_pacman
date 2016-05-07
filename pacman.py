import nengo
import pacman_world

# Adjust this to generate new maps.
# key: # - Wall
#      S - Starting location for player
#      E - Starting location for enemies
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
    
    # create the movement control
    # - dimensions are speed (forward|backward) and rotation (left|right)
    move = nengo.Ensemble(n_neurons=100, dimensions=2, radius=3)
    nengo.Connection(move, pacman.move)
    
    # sense food
    # - angle is the direction to the food
    # - radius is the strength (1.0/distance)
    food = nengo.Ensemble(n_neurons=100, dimensions=2)
    nengo.Connection(pacman.detect_food, food)
    
    # go towards food
    nengo.Connection(food[0], move[1])
    

    # sense obstacles
    # - distance to obstacles on left, front-left, front, front-right, and right
    # - maximum distance is 4
    obstacles = nengo.Ensemble(n_neurons=300, dimensions=3, radius=4)
    nengo.Connection(pacman.obstacles[[1, 2, 3]], obstacles)
    
    # turn away from walls
    def avoid(x):
        return 1*(x[2] - x[0])
    nengo.Connection(obstacles, move[1], function=avoid)
    
    # avoid crashing into walls
    def ahead(x):
        return 1*(x[1] - 0.5)
    nengo.Connection(obstacles, move[0], function=ahead)
    
    # detect enemies
    enemy = nengo.Ensemble(n_neurons=100, dimensions=2)
    nengo.Connection(pacman.detect_enemy, enemy)
    
    # run away from enemies
    # - angle is the direction to the enemies
    # - radius is the strength (1.0/distance)
    def run_away(x):
        return -2*x[1], -2*x[0]
    nengo.Connection(enemy, move, function=run_away)
        

