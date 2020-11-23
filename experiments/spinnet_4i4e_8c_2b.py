import os

import spinnaker_graph_front_end as gfe

from pacman.model.graphs.machine import MachineEdge

from pkt_injector_vertex import Pkt_Injector_Vertex
from pkt_extractor_vertex import Pkt_Extractor_Vertex


# throttle injectors to avoid dropped packets
OUTSIDE_INJECTOR_THROTTLE = [46, 47, 48, 47, 46, 47, 47, 47]
INSIDE_INJECTOR_THROTTLE  = [46, 47, 48, 47, 46, 47, 47, 47]
#UTSIDE_INJECTOR_THROTTLE = [47, 47, 47, 47, 47, 47, 47, 47]
#NSIDE_INJECTOR_THROTTLE  = [47, 47, 47, 47, 47, 47, 47, 47]

# number of chips to connect
NUM_CHIPS = 8

# number of injectors per chip
NUM_INJECTORS = 4

# chips on neighbouring board across FPGA2 (using SpiNNaker link 1)
OUTSIDE_CHIPS = [(5, 8), (6, 8), (7, 8), (8, 8),
         (8, 7), (8, 6), (8, 5), (8, 4)]

# chips on board border connected to FPGA2
INSIDE_CHIPS = [(4, 7), (5, 7), (6, 7), (7, 7),
         (7, 6), (7, 5), (7, 4), (7, 3)]

# make sure to get two neighbouring boards across FPGA2
gfe.setup(
    machine_time_step   = 1000000,
    n_boards_required   = 3,
    model_binary_folder = os.path.dirname(__file__)+"/.."
    )

# create connections along the border
for n in range(NUM_CHIPS):
    for i in range(NUM_INJECTORS):
        # instantiate inside-out injector vertex
        (xi, yi) = INSIDE_CHIPS[n]

        iv = Pkt_Injector_Vertex(
            x_coord  = xi,
            y_coord  = yi,
            throttle = INSIDE_INJECTOR_THROTTLE[n]
            )

        gfe.add_machine_vertex_instance(iv)

        # instantiate inside-out extractor vertex
        (xe, ye) = OUTSIDE_CHIPS[n]
        ev = Pkt_Extractor_Vertex(x_coord = xe, y_coord = ye)
        gfe.add_machine_vertex_instance(ev)

        # create link from injector to extractor
        gfe.add_machine_edge_instance(MachineEdge (iv, ev), iv.inj_lnk)

        # instantiate outside-in injector vertex
        (xi, yi) = OUTSIDE_CHIPS[n]

        iv = Pkt_Injector_Vertex(
            x_coord  = xi,
            y_coord  = yi,
            throttle = OUTSIDE_INJECTOR_THROTTLE[n]
            )

        gfe.add_machine_vertex_instance(iv)

        # instantiate outside-in extractor vertex
        (xe, ye) = INSIDE_CHIPS[n]
        ev = Pkt_Extractor_Vertex(x_coord = xe, y_coord = ye)
        gfe.add_machine_vertex_instance(ev)

        # create link from injector to extractor
        gfe.add_machine_edge_instance(MachineEdge (iv, ev), iv.inj_lnk)

# run experiment
gfe.run(10000)

# pause to allow external debugging
#input ("experiment paused: press enter to continue")

# finish
gfe.stop()
