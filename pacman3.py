import nengo
import pm
import numpy as np
import random

seed = 13   #3 5 6 7 ## 8, 11, 12?, 16
random.seed(seed)
np.random.seed(seed)

model = nengo.Network(seed=seed)

with model:
    pacman = pm.pacman_world.PacmanWorld(
        pm.maze.generateMaze(num_rows=4,
                             num_cols=4, 
                             num_ghosts=1,
                             num_passage=3,
                             seed=0))

    move = nengo.Ensemble(n_neurons=100, dimensions=2, radius=3)
    nengo.Connection(move, pacman.move, synapse = 0.)

    food = nengo.Ensemble(n_neurons=100, dimensions=2)
    nengo.Connection(pacman.detect_food, food, synapse = 0.)

    def go_food(x):
        food_angle = x[0]
        food_distance = x[1]
        turn = food_angle * 5
        speed = food_distance * 3
        return speed, turn
    nengo.Connection(food, move, function=go_food)

    obstacles = nengo.Ensemble(n_neurons=50, dimensions=3, radius=4)
    nengo.Connection(pacman.obstacles, obstacles, transform=0.5, synapse = 0.)

    def avoid_obstacles(x):
        distance_left, distance_ahead, distance_right = x
        turn = 1 * (distance_right - distance_left)
        speed = 1 * (distance_ahead - 0.5)
        return speed, turn
    nengo.Connection(obstacles, move, 
            function=avoid_obstacles)

    enemy = nengo.Ensemble(n_neurons=50, dimensions=2)
    nengo.Connection(pacman.detect_enemy, enemy, synapse = 0)

    def run_away(x):
        enemy_angle = x[0]
        enemy_closeness = x[1]
        turn = enemy_angle * -5
        speed = enemy_closeness * - 20
        return speed, turn
    nengo.Connection(enemy, move, function=run_away)