import os

import spinnaker_graph_front_end as gfe

from pacman.model.graphs.machine import MachineEdge

from pkt_injector_vertex import Pkt_Injector_Vertex
from pkt_extractor_vertex import Pkt_Extractor_Vertex


# number of connections to test
NUM_CONNECTIONS = 8

# number of injectors per chip
NUM_INJECTORS = 4

# test INSIDE-OUT connections
#NOTE: this tests model peripheral output
DO_INSIDE_OUT = 1

# test OUTSIDE_IN connections
#NOTE: this tests model peripheral input
DO_OUTSIDE_IN = 0

# chips on board border connected to FPGA0
INSIDE_CHIPS  = [(4, 8), (5, 8), (6, 8), (7, 8), (8, 8), (9, 9), (10, 10), (11, 11)]

# chips on neighbouring board across FPGA0 (using SpiNNaker link 2 - NORTH)
OUTSIDE_CHIPS = [(4, 7), (5, 7), (6, 7), (7, 7), (8, 7), (9, 8), (10, 9), (11, 10)]

# throttle injectors to avoid dropped packets
INSIDE_INJECTOR_THROTTLE  = [32, 32, 32, 32, 32, 32, 32, 32]
OUTSIDE_INJECTOR_THROTTLE = [32, 32, 32, 32, 32, 32, 32, 32]

# make sure to get two neighbouring boards across FPGA2
gfe.setup(
    machine_time_step   = 1000000,
    n_boards_required   = 3,
    model_binary_folder = os.path.dirname(__file__)+"/.."
    )

# create connections along the border
for n in range(NUM_CONNECTIONS):
    # inside chip coordinates
    (xin, yin) = INSIDE_CHIPS[n]

    # outside chip coordinates
    (xout, yout) = OUTSIDE_CHIPS[n]

    for i in range(NUM_INJECTORS):
        if DO_INSIDE_OUT:
            # instantiate inside-out injector vertex
            iv = Pkt_Injector_Vertex(
                x_coord  = xin,
                y_coord  = yin,
                throttle = INSIDE_INJECTOR_THROTTLE[n]
                )
            gfe.add_machine_vertex_instance(iv)

            # instantiate inside-out extractor vertex
            ev = Pkt_Extractor_Vertex(
                x_coord = xout,
                y_coord = yout
                )
            gfe.add_machine_vertex_instance(ev)

            # create link from injector to extractor
            gfe.add_machine_edge_instance(MachineEdge (iv, ev), iv.inj_lnk)

        if DO_OUTSIDE_IN:
            # instantiate outside-in injector vertex
            iv = Pkt_Injector_Vertex(
                x_coord  = xout,
                y_coord  = yout,
                throttle = OUTSIDE_INJECTOR_THROTTLE[n]
                )
            gfe.add_machine_vertex_instance(iv)

            # instantiate outside-in extractor vertex
            ev = Pkt_Extractor_Vertex(
                x_coord = xin,
                y_coord = yin)
            gfe.add_machine_vertex_instance(ev)

            # create link from injector to extractor
            gfe.add_machine_edge_instance(MachineEdge (iv, ev), iv.inj_lnk)

# run experiment
gfe.run(10000)

# pause to allow external debugging
input ("experiment paused: press enter to continue")

# finish
gfe.stop()
