import os

import spinnaker_graph_front_end as gfe

from pacman.model.graphs.machine import MachineEdge

from pkt_injector_vertex import Pkt_Injector_Vertex
from pkt_extractor_vertex import Pkt_Extractor_Vertex


gfe.setup(
    machine_time_step = 1000000,
    n_chips_required = 1,
    model_binary_folder=os.path.dirname(__file__)
    )

# instantiate injector vertex
iv = Pkt_Injector_Vertex()
gfe.add_machine_vertex_instance(iv)

# instantiate extractor vertex
ev = Pkt_Extractor_Vertex()
gfe.add_machine_vertex_instance(ev)

# create link from injector to extractor
gfe.add_machine_edge_instance (MachineEdge (iv, ev), iv.inj_lnk)

gfe.run(10000)

gfe.stop()
