import nengo
import pm

model = nengo.Network()

with model:
    pacman = pm.pacman_world.PacmanWorld(
                    pm.maze.generateMaze(num_rows=2, num_cols=2, num_passage=20,
                                         empty=True,
                                         num_ghosts=0, seed=1))

    move = nengo.Ensemble(n_neurons=100, dimensions=2, radius=3)
    nengo.Connection(move, pacman.move, synapse = 0.)

    food = nengo.Ensemble(n_neurons=100, dimensions=2)
    nengo.Connection(pacman.detect_food, food, synapse = 0.)

    def go_food(x):
        food_angle = x[0]
        food_distance = x[1]
        turn = food_angle * 10
        speed = 1
        return speed, turn
        
    nengo.Connection(food, move, function=go_food)

