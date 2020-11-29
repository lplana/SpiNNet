import os
import sys

import spinnaker_graph_front_end as gfe

from pacman.model.graphs.machine import MachineEdge

from pkt_injector_vertex import Pkt_Injector_Vertex
from pkt_extractor_vertex import Pkt_Extractor_Vertex


# number of connections to test
NUM_CONNECTIONS = 8

# number of injectors per connection
NUM_INJECTORS_PER_CONNECTION = 4

# use payloads to verify arrival of all packets
USE_PAYLOADS = True

# test southward connections (SpiNNaker link 5)
TEST_S = 1

# test eastward and southwestward connections (SpiNNaker links 0 & 4)
TEST_E_SW = 1

# test INSIDE-OUT connections
#NOTE: this tests model peripheral output
DO_INSIDE_OUT = 1

# test OUTSIDE_IN connections
#NOTE: this tests model peripheral input
DO_OUTSIDE_IN = 1

if (not TEST_S and not TEST_E_SW) or (not DO_INSIDE_OUT and not DO_OUTSIDE_IN):
    sys.exit ("error: no connections to test")

# chips on board border connected to FPGA0 (S connections)
INSIDE_CHIPS_S  = [(4, 8), (5, 8), (6, 8), (7, 8), (8, 8), (9, 9), (10, 10), (11, 11)]

# chips on neighbouring board across FPGA0 (using SpiNNaker link 5 - SOUTH)
OUTSIDE_CHIPS_S = [(4, 7), (5, 7), (6, 7), (7, 7), (8, 7), (9, 8), (10, 9), (11, 10)]

# chips on board border connected to FPGA0 (E-SW connections)
INSIDE_CHIPS_E_SW  = [(5, 8), (6, 8), (7, 8), (8, 8), (8, 8), (9, 9), (10, 10), (11, 11)]

# chips on neighbouring board across FPGA0 (using SpiNNaker links 0 - EAST & 4 - SOUTHWEST)
OUTSIDE_CHIPS_E_SW = [(4, 7), (5, 7), (6, 7), (7, 7), (9, 8), (10, 9), (11, 10), (12, 11)]

if TEST_S:
    if TEST_E_SW:
        HALF_CONN = NUM_CONNECTIONS // 2
        INSIDE_CHIPS = INSIDE_CHIPS_S[0 : HALF_CONN]
        INSIDE_CHIPS.extend(INSIDE_CHIPS_E_SW[0 : HALF_CONN])

        OUTSIDE_CHIPS = OUTSIDE_CHIPS_S[0 : HALF_CONN]
        OUTSIDE_CHIPS.extend(OUTSIDE_CHIPS_E_SW[0 : HALF_CONN])
    else:        
        INSIDE_CHIPS  = INSIDE_CHIPS_S
        OUTSIDE_CHIPS = OUTSIDE_CHIPS_S
elif TEST_E_SW:
    INSIDE_CHIPS  = INSIDE_CHIPS_E_SW
    OUTSIDE_CHIPS = OUTSIDE_CHIPS_E_SW
else:
    sys.exit ("error: no connections to test")

# throttle injectors to avoid dropped packets
#NOTE: [master_1.0.0]    [46] 3802278 - no NAKs
#NOTE: [master_SA_1.0.1] [46] 3802278 - no NAKs
INSIDE_INJECTOR_THROTTLE  = [8, 8, 8, 8, 8, 8, 8, 8]

#NOTE: [master_1.0.0]    [54] 3300327 - no NAKs
#NOTE: [master_SA_1.0.1] [54] 3300327 - no NAKs
#NOTE: [master_1.0.0]    [48] (3409224, 3409237) 2727363 NAKs/38 dropped
#NOTE: [master_SA_1.0.1] [48] (3348700, 3409284) 2697373 NAKs/10982 dropped
OUTSIDE_INJECTOR_THROTTLE = [8, 8, 8, 8, 8, 8, 8, 8]

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

    for i in range(NUM_INJECTORS_PER_CONNECTION):
        if DO_INSIDE_OUT:
            # instantiate inside-out injector vertex
            iv = Pkt_Injector_Vertex(
                x_coord     = xin,
                y_coord     = yin,
                throttle    = INSIDE_INJECTOR_THROTTLE[n],
                use_payload = USE_PAYLOADS
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
                throttle = OUTSIDE_INJECTOR_THROTTLE[n],
                use_payload = USE_PAYLOADS
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
