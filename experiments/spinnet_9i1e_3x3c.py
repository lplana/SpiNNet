import os

import spinnaker_graph_front_end as gfe

from pacman.model.graphs.machine import MachineEdge

from pkt_injector_vertex import Pkt_Injector_Vertex
from pkt_extractor_vertex import Pkt_Extractor_Vertex


# populate a square region of chips
X_CHIPS = 3
Y_CHIPS = 3
CHIPS = []
for x in range (X_CHIPS):
    for y in range (Y_CHIPS):
        CHIPS.append ((x, y))

# populate each chip with this number of packet injectors
NUM_INJECTORS = len (CHIPS)


gfe.setup(
    machine_time_step = 1000000,
    n_chips_required = len (CHIPS),
    model_binary_folder=os.path.dirname(__file__)
    )

for (x_coord, y_coord) in CHIPS:
    # instantiate extractor vertex on chip
    ev = Pkt_Extractor_Vertex(x_coord = x_coord, y_coord = y_coord)
    gfe.add_machine_vertex_instance(ev)

    # instantiate injector vertices on chip
    for i in range (NUM_INJECTORS):
        iv = Pkt_Injector_Vertex(i, x_coord = x_coord, y_coord = y_coord)
        gfe.add_machine_vertex_instance(iv)

        # create links from injectors to extractor on same chip
        gfe.add_machine_edge_instance (MachineEdge (iv, ev), iv.inj_lnk)

gfe.run(10000)

gfe.stop()
