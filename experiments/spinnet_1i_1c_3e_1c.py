import os

import spinnaker_graph_front_end as gfe

from pacman.model.graphs.machine import MachineEdge

from pkt_injector_vertex import Pkt_Injector_Vertex
from pkt_extractor_vertex import Pkt_Extractor_Vertex


# tuple indices for coordinates
X = 0
Y = 1

# populate this chip with a packet injector
INJECTOR = (0, 0)

# populate each chip with this number of packet extractors
EXTRACTORS = {(1, 0) : 3}


gfe.setup(
    machine_time_step = 1000000,
    n_chips_required = len (EXTRACTORS) + 1,
    model_binary_folder=os.path.dirname(__file__)
    )

# compute total number of extractor vertices
NUM_EXTRACTORS = 0
for chip, ne in EXTRACTORS.items():
    NUM_EXTRACTORS += ne

# instantiate injector vertex
iv = Pkt_Injector_Vertex(
    x_coord = INJECTOR[X], y_coord = INJECTOR[Y],
    nkeys = NUM_EXTRACTORS)

gfe.add_machine_vertex_instance(iv)

# instantiate extractor vertices
lnk = 0
for chip, ne in EXTRACTORS.items():
    for e in range (ne):
        ev = Pkt_Extractor_Vertex(iid = e, x_coord = chip[X], y_coord = chip[Y])
        gfe.add_machine_vertex_instance(ev)

        # create link from injector to extractor
        gfe.add_machine_edge_instance (MachineEdge (iv, ev), iv.inj_lnk[lnk])
        lnk += 1

gfe.run(10000)

gfe.stop()
