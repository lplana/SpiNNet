import os
import sys

import spinnaker_graph_front_end as gfe

from pacman.model.graphs.machine import MachineEdge

from pkt_injector_vertex import Pkt_Injector_Vertex
from pkt_extractor_vertex import Pkt_Extractor_Vertex


# Send packets in both directions (FX -> FY and FY -> FX)
BIDIRECTIONAL = True

# number of connections to test
NUM_CONNECTIONS = 8

# number of injectors per connection
NUM_INJECTORS_PER_CONNECTION = 4

# use payloads to verify arrival of all packets
USE_PAYLOADS = True

# test two connected FPGAs
FX = 0
FY = 2

if FX == FY:
    sys.exit (f"error: cannot test FPGA{FX} on its own")
elif FX > FY:
    tmp = FY
    FY  = FX
    FX  = tmp

# define FX and FY chips on experiment
if FX == 0:
    if FY == 1:
        FX_CHIPS = [(8, 8), (9, 9), (10, 10), (11, 11), (8, 8), ( 9, 9), (10, 10), (11, 11)]
        FY_CHIPS = [(8, 7), (9, 8), (10,  9), (11, 10), (9, 8), (10, 9), (11, 10), (12, 11)]
    else:
        FX_CHIPS = [(4, 8), (5, 8), (6, 8), (7, 8), (5, 8), (6, 8), (7, 8), (8, 8)]
        FY_CHIPS = [(4, 7), (5, 7), (6, 7), (7, 7), (4, 7), (5, 7), (6, 7), (7, 7)]
else:
    # test F1 and F2
    FX_CHIPS = [(8, 4), (8, 5), (8, 6), (8, 7), (8, 4), (8, 5), (8, 6), (8, 7)]
    FY_CHIPS = [(7, 4), (7, 5), (7, 6), (7, 7), (7, 3), (7, 4), (7, 5), (7, 6)]

# throttle injectors to avoid dropped packets
if BIDIRECTIONAL:
    #NOTE: 53 [MPS_QIO_F8_1.0.1] no NAKs
    FX_INJECTOR_THROTTLE  = [52, 52, 52, 52, 52, 52, 52, 52]
    FY_INJECTOR_THROTTLE = [52, 52, 52, 52, 52, 52, 52, 52]
else:
    #NOTE: 48 [MPS_QIO_F8_1.0.1] no NAKs PLD CON=4
    FX_INJECTOR_THROTTLE  = [48, 48, 48, 48, 48, 48, 48, 48]

# make sure to get two neighbouring boards across FPGA2
gfe.setup(
    machine_time_step   = 1000000,
    n_boards_required   = 3,
    model_binary_folder = os.path.dirname(__file__)+"/.."
    )

# create connections along the border
for n in range(NUM_CONNECTIONS):
    # FX chip coordinates
    (xx, yx) = FX_CHIPS[n]

    # FY chip coordinates
    (xy, yy) = FY_CHIPS[n]

    for i in range(NUM_INJECTORS_PER_CONNECTION):
        # instantiate FX injector vertex
        iv = Pkt_Injector_Vertex(
            x_coord     = xx,
            y_coord     = yx,
            throttle    = FX_INJECTOR_THROTTLE[n],
            use_payload = USE_PAYLOADS
            )
        gfe.add_machine_vertex_instance(iv)

        # instantiate FY extractor vertex
        ev = Pkt_Extractor_Vertex(
            x_coord = xy,
            y_coord = yy
            )
        gfe.add_machine_vertex_instance(ev)

        # create link from injector to extractor
        gfe.add_machine_edge_instance(MachineEdge (iv, ev), iv.inj_lnk)

        if BIDIRECTIONAL:
            # instantiate FY injector vertex
            iv = Pkt_Injector_Vertex(
                x_coord  = xy,
                y_coord  = yy,
                throttle = FY_INJECTOR_THROTTLE[n],
                use_payload = USE_PAYLOADS
                )
            gfe.add_machine_vertex_instance(iv)

            # instantiate FX extractor vertex
            ev = Pkt_Extractor_Vertex(
                x_coord = xx,
                y_coord = yx
                )
            gfe.add_machine_vertex_instance(ev)

            # create link from injector to extractor
            gfe.add_machine_edge_instance(MachineEdge (iv, ev), iv.inj_lnk)

# run experiment
gfe.run(10000)

# pause to allow external debugging
input ("experiment paused: press enter to continue")

# finish
gfe.stop()
