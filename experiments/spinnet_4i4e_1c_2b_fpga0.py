import os

import spinnaker_graph_front_end as gfe

from pacman.model.graphs.machine import MachineEdge

from pkt_injector_vertex import Pkt_Injector_Vertex
from pkt_extractor_vertex import Pkt_Extractor_Vertex


# number of chips to connect
NUM_CHIPS = 2

# number of injectors per chip
NUM_INJECTORS = 4

# chips on board border connected to FPGA2
INSIDE_CHIPS  = [(4, 8), (5, 8)]

# chips on neighbouring board across FPGA2 (using SpiNNaker link 1)
OUTSIDE_CHIPS = [(4, 7), (5, 7)]

# throttle injectors to avoid dropped packets
OUTSIDE_INJECTOR_THROTTLE = [56, 56]
INSIDE_INJECTOR_THROTTLE  = [56, 56]

# make sure to get two neighbouring boards across FPGA2
gfe.setup(
    machine_time_step   = 1000000,
    n_boards_required   = 3,
    model_binary_folder = os.path.dirname(__file__)+"/.."
    )

# create connections along the border
for n in range(NUM_CHIPS):
    # inside chip coordinates and parameters
    (xin, yin)  = INSIDE_CHIPS[n]
    throttle_in = INSIDE_INJECTOR_THROTTLE[n]

    # outside chip coordinates and parameters
    (xout, yout) = OUTSIDE_CHIPS[n]
    throttle_out = OUTSIDE_INJECTOR_THROTTLE[n]

    for i in range(NUM_INJECTORS):
        # instantiate inside-out injector vertex
        iv = Pkt_Injector_Vertex(
            x_coord  = xin,
            y_coord  = yin,
            throttle = throttle_in
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

        # instantiate outside-in injector vertex
        iv = Pkt_Injector_Vertex(
            x_coord  = xout,
            y_coord  = yout,
            throttle = throttle_out
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
