import nengo
import pacman_world
#reload(pacman_world)
import numpy as np
import re
import body
import maze

# Nengo Network
model = nengo.Network()
mymap = maze.generateMaze(num_rows=5, num_cols=5, num_ghosts=1)

# Initliazing the nengo model, network and game map

with model:

    pacman = pacman_world.PacmanWorld(mymap)

    # create the movement control
    # - dimensions are speed (forward|backward) and rotation (left|right)
    moveSensor = nengo.Node(size_in = 2)
    move = nengo.Ensemble(n_neurons=100, dimensions=2, radius=3)

    nengo.Connection(move, moveSensor, synapse = 0.)
    nengo.Connection(moveSensor, pacman.move, synapse = 0.)

    # sense food
    # - angle is the direction to the food
    # - radius is the strength (1.0/distance)
    foodSensor = nengo.Node(size_in = 2)
    nengo.Connection(pacman.detect_food, foodSensor, synapse = 0.)

    food = nengo.Ensemble(n_neurons=100, dimensions=2)
    nengo.Connection(foodSensor, food, synapse = 0.)

    # turn towards food
    nengo.Connection(food[0], move[1], transform=2)
    # move towards food
    nengo.Connection(food[1], move[0], transform=3)

    # sense obstacles
    # - distance to obstacles on left, front-left, front, front-right, and right
    # - maximum distance is 4
    obstacleSensor = nengo.Node(size_in = 3)
    obstacles = nengo.Ensemble(n_neurons=50, dimensions=3, radius=4)
    nengo.Connection(pacman.obstacles[[1,2,3]], obstacleSensor, transform=0.5, synapse = 0.)
    nengo.Connection(obstacleSensor, obstacles, synapse = 0.)

    # turn away from walls
    def avoid(x):
        return 1*(x[2] - x[0])
    nengo.Connection(obstacles, move[1], function=avoid)

    # avoid crashing into walls
    def ahead(x):
        return 1*(x[1] - 0.5)
    nengo.Connection(obstacles, move[0], function=ahead)

    # detect enemies
    enemySensor = nengo.Node(size_in = 2)
    nengo.Connection(pacman.detect_enemy, enemySensor, synapse = 0.)

    enemy = nengo.Ensemble(n_neurons=50, dimensions=2)
    nengo.Connection(enemySensor, enemy, synapse = 0.)

    # run away from enemies
    # - angle is the direction to the enemies
    # - radius is the strength (1.0/distance)
    def run_away(x):
        return -1*x[1], -1*x[0]
    nengo.Connection(enemy, move, function=run_away, transform=3)
