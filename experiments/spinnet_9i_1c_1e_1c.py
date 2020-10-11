import os

import spinnaker_graph_front_end as gfe

from pacman.model.graphs.machine import MachineEdge

from pkt_injector_vertex import Pkt_Injector_Vertex
from pkt_extractor_vertex import Pkt_Extractor_Vertex


# tuple indices for coordinates
X = 0
Y = 1

# populate this chip with a packet injector
INJECTORS = {(0, 0) : 9}

# populate each chip with this number of packet extractors
EXTRACTOR = (1, 0)


gfe.setup(
    machine_time_step = 1000000,
    n_chips_required = len (INJECTORS) + 1,
    model_binary_folder=os.path.dirname(__file__)
    )

# instantiate extractor vertex
ev = Pkt_Extractor_Vertex(x_coord = EXTRACTOR[X], y_coord = EXTRACTOR[Y])
gfe.add_machine_vertex_instance(ev)

for chip, ni in INJECTORS.items():
    for i in range (ni):
        iv = Pkt_Injector_Vertex(iid = i, x_coord = chip[X], y_coord = chip[Y])
        gfe.add_machine_vertex_instance(iv)

        # create link from injector to extractor
        gfe.add_machine_edge_instance (MachineEdge (iv, ev), iv.inj_lnk)

gfe.run(10000)

gfe.stop()
