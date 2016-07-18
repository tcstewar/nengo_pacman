import nengo
import pm
import numpy as np

model = nengo.Network()

with model:
    pacman = pm.pacman_world.PacmanWorld(
                    pm.maze.generateMaze(num_rows=5, num_cols=5, 
                                         num_ghosts=1, seed=1))

    move = nengo.Ensemble(n_neurons=100, dimensions=2, radius=3)
    nengo.Connection(move, pacman.move, synapse = 0.)

    food = nengo.Ensemble(n_neurons=100, dimensions=2)
    nengo.Connection(pacman.detect_food, food, synapse = 0.)

    food_move = nengo.Node(size_in=2)
    nengo.Connection(food_move, move, synapse=0)

    # turn towards food
    nengo.Connection(food[0], food_move[1], transform=5)
    # move towards food
    nengo.Connection(food[1], food_move[0], transform=3)

    obstacles = nengo.Ensemble(n_neurons=50, dimensions=3, radius=4)
    nengo.Connection(pacman.obstacles, obstacles, transform=0.5, synapse = 0.)

    obstacle_move = nengo.Node(size_in=2)
    nengo.Connection(obstacle_move, move, synapse=0)


    # turn away from walls
    def avoid(x):
        return 1*(x[2] - x[0])
    nengo.Connection(obstacles, obstacle_move[1], function=avoid)

    # avoid crashing into walls
    def ahead(x):
        return 1*(x[1] - 0.5)
    nengo.Connection(obstacles, obstacle_move[0], function=ahead)


    enemy = nengo.Ensemble(n_neurons=50, dimensions=2)
    nengo.Connection(pacman.detect_enemy, enemy, synapse = 0.)

    fear_move = nengo.Node(size_in=2)
    nengo.Connection(fear_move, move, synapse=0)


    def run_away(x):
        return -20*x[1], -5*x[0]
    nengo.Connection(enemy, fear_move, function=run_away, transform=1)


    ignore_food = nengo.Node(0)
    nengo.Connection(ignore_food, food.neurons, transform=np.ones((food.n_neurons,1))*-3)

    ignore_enemy = nengo.Node(0)
    nengo.Connection(ignore_enemy, enemy.neurons, transform=np.ones((enemy.n_neurons,1))*-3)    
    
    ignore_obstacles = nengo.Node(0)
    nengo.Connection(ignore_obstacles, obstacles.neurons, transform=np.ones((obstacles.n_neurons,1))*-3)        