import struct
from enum import Enum

from data_specification.enums.data_type import DataType

from pacman.model.graphs.machine.machine_vertex import MachineVertex
from pacman.model.resources.resource_container \
    import ResourceContainer, ConstantSDRAM
from pacman.model.constraints.placer_constraints import ChipAndCoreConstraint

from spinn_front_end_common.abstract_models.impl \
    import MachineDataSpecableVertex
from spinn_front_end_common.utilities.constants \
    import SYSTEM_BYTES_REQUIREMENT

from spinnaker_graph_front_end.utilities import SimulatorVertex
from spinnaker_graph_front_end.utilities.data_utils \
    import generate_system_data_region

from spinn_utilities.overrides import overrides


class Pkt_Extractor_Vertex(
        SimulatorVertex,
        MachineDataSpecableVertex
        ):

    """ A packet extractor for SpiNNaker network traffic tests
    """

    SDRAM_REGIONS = Enum(
        value="SDRAM_REGIONS",
        names=[('SYSTEM',    0),
               ('EXTRACTOR', 1)
               ]
        )


    def __init__(self,
                 iid = 0,
                 x_coord = None,
                 y_coord = None
                 ):


        label = f"pe/{iid}"
        constraints = None
        if x_coord is not None:
            if y_coord is not None:
                label = f"pe/{x_coord}-{y_coord}/{iid}"
                constraints = [ChipAndCoreConstraint(
                    x = int (x_coord),
                    y = int (y_coord)
                    )]
            else:
                print ("incompatible coordinates given")
        elif y_coord is not None:
                print ("incompatible coordinates given")

        super(Pkt_Extractor_Vertex, self).__init__(
            label = label,
            binary_name = "pkt_extractor.aplx",
            constraints = constraints
            )

        # configuration structure
        self.CONFIGURATION_BYTES = len (self.config)

        # configuration data plus application core SDRAM usage
        self.sdram_fixed = (
            SYSTEM_BYTES_REQUIREMENT +
            self.CONFIGURATION_BYTES
        )


    @property
    def config (self):
        """ returns a packed string that corresponds to
            (C struct) extractor_conf in pkt_extractor.c:

            typedef struct extractor_conf {
              uint32_t throttle;         // extraction slow down
              uint32_t active_time;      // length of time for packet extraction
            } extractor_conf_t;

            pack: standard sizes, little-endian byte order,
            explicit padding
        """
        throttle      = 0
        active_time   = 9

        return struct.pack ("<2I",
                            throttle,
                            active_time
                            )

    @property
    @overrides (MachineVertex.resources_required)
    def resources_required (self):
        resources = ResourceContainer (
            sdram = ConstantSDRAM(self.sdram_fixed)
            )
        return resources


    @overrides(MachineDataSpecableVertex.generate_machine_data_specification)
    def generate_machine_data_specification(
            self, spec, placement, machine_graph, routing_info, iptags,
            reverse_iptags, machine_time_step, time_scale_factor):

        # Generate the system data region for simulation.c requirements
        generate_system_data_region(spec, self.SDRAM_REGIONS.SYSTEM.value,
                                    self, machine_time_step, time_scale_factor)

        # reserve and write the core configuration region
        spec.reserve_memory_region (self.SDRAM_REGIONS.EXTRACTOR.value,
                                    self.CONFIGURATION_BYTES)

        spec.switch_write_focus (self.SDRAM_REGIONS.EXTRACTOR.value)

        # write the core configuration into spec
        for c in self.config:
            spec.write_value (c, data_type = DataType.UINT8)

        spec.end_specification()
