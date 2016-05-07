import nengo

import pacman_world
reload(pacman_world)

mymap="""
#######
#  S  #
#     #
#     #
# ##  #
#  E  #
#######
"""

model = nengo.Network()
with model:
    pacman = pacman_world.PacmanWorld(mymap)
    
    manual_control = nengo.Node([0, 0])
    nengo.Connection(manual_control, pacman.move)

