import os

import spinnaker_graph_front_end as gfe

from pacman.model.graphs.machine import MachineEdge

from pkt_injector_vertex import Pkt_Injector_Vertex
from pkt_extractor_vertex import Pkt_Extractor_Vertex


# populate a line of chips with injectors and extractors
INJECTORS = [(0, 0), (1, 1), (2, 2), (3, 3), (4, 4), (5, 5), (6, 6), (7, 7)]

EXTRACTORS = [(8, 8), (9, 9), (10, 10), (11, 11),
              (12, 12), (13, 13), (14, 14), (15, 15)]

# populate each INJECTOR chip with an injector for every extractor
NUM_INJECTORS = len (EXTRACTORS)

gfe.setup(
    machine_time_step = 1000000,
    n_boards_required = 12,
    model_binary_folder=os.path.dirname(__file__)
    )

# place an extractor on every EXTRACTOR chip
extractors = []
for (x_coord, y_coord) in EXTRACTORS:
    ev = Pkt_Extractor_Vertex(x_coord = x_coord, y_coord = y_coord)
    gfe.add_machine_vertex_instance(ev)
    extractors.append (ev)

# place injectors on every INJECTOR chip
for (x_coord, y_coord) in INJECTORS:
    for i in range (NUM_INJECTORS):
        # instantiate injector on chip
        iv = Pkt_Injector_Vertex(i, x_coord = x_coord, y_coord = y_coord)
        gfe.add_machine_vertex_instance(iv)

        # create link to the corresponding extractor
        ev = extractors[i]
        gfe.add_machine_edge_instance (MachineEdge (iv, ev), iv.inj_lnk)

gfe.run(10000)

gfe.stop()
