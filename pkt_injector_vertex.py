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
    import SYSTEM_BYTES_REQUIREMENT, BYTES_PER_WORD

from spinnaker_graph_front_end.utilities import SimulatorVertex
from spinnaker_graph_front_end.utilities.data_utils \
    import generate_system_data_region

from spinn_utilities.overrides import overrides


class Pkt_Injector_Vertex(
        SimulatorVertex,
        MachineDataSpecableVertex
        ):

    """ A packet injector for SpiNNaker network traffic tests
    """

    SDRAM_REGIONS = Enum(
        value="SDRAM_REGIONS",
        names=[('SYSTEM',   0),
               ('INJECTOR', 1),
               ('ROUTING',  2)
               ]
        )


    def __init__(self,
                 iid = 0,
                 x_coord  = None,
                 y_coord  = None,
                 nkeys    = 1,
                 throttle = 0
                 ):

        label = f"pi/{iid}"
        constraints = None
        if x_coord is not None:
            if y_coord is not None:
                label = f"pi/{x_coord}-{y_coord}/{iid}"
                constraints = [ChipAndCoreConstraint(
                    x = int (x_coord),
                    y = int (y_coord)
                    )]
            else:
                print ("incompatible coordinates given")
        elif y_coord is not None:
                print ("incompatible coordinates given")

        super(Pkt_Injector_Vertex, self).__init__(
            label = label,
            binary_name = "pkt_injector.aplx",
            constraints = constraints
            )

        # number of routing keys to be used
        self.NKEYS = nkeys

        # injection links
        if self.NKEYS == 1:
            self.inj_lnk = f"inj_link{x_coord}-{y_coord}/{iid}"
        else:
            self.inj_lnk = []
            for k in range (self.NKEYS):
                self.inj_lnk.append (f"inj_link{x_coord}-{y_coord}/{iid}/{k}")

        # number of routing keys to be used
        self.throttle = throttle

        # size of configuration structure in SDRAM
        self.CONFIGURATION_BYTES = len (self.config)

        # size of routing keys structure in SDRAM
        self.ROUTING_BYTES = (self.NKEYS + 1) * BYTES_PER_WORD

        # total SDRAM usage
        self.sdram_fixed = (
            SYSTEM_BYTES_REQUIREMENT +
            self.CONFIGURATION_BYTES +
            self.ROUTING_BYTES
        )


    @property
    def config (self):
        """ returns a packed string that corresponds to
            (C struct) injector_conf in pkt_injector.c:

            typedef struct injector_conf {
              uint32_t throttle;       // injection slow down
              uint32_t active_time;    // length of time for packet sending
              uint32_t delayed_start;  // delay the start of packet sending
              uint32_t idle_end;       // idle time after packet sending stops
              uint32_t use_payload;      // send packets with sequential payloads
            } injector_conf_t;

            pack: standard sizes, little-endian byte order,
            explicit padding
        """
        active_time   = 5
        delayed_start = 2
        idle_end      = 3

        use_payload   = 1

        return struct.pack ("<5I",
                            self.throttle,
                            active_time,
                            delayed_start,
                            idle_end,
                            use_payload
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
        spec.reserve_memory_region (self.SDRAM_REGIONS.INJECTOR.value,
                                    self.CONFIGURATION_BYTES)

        spec.switch_write_focus (self.SDRAM_REGIONS.INJECTOR.value)

        # write core configuration into spec
        for c in self.config:
            spec.write_value (c, data_type = DataType.UINT8)

        # reserve and write the routing keys region
        spec.reserve_memory_region (self.SDRAM_REGIONS.ROUTING.value,
                                    self.ROUTING_BYTES)

        spec.switch_write_focus (self.SDRAM_REGIONS.ROUTING.value)

        # write number of routing keys
        spec.write_value (self.NKEYS, data_type = DataType.UINT32)

        # write routing keys
        if self.NKEYS == 1:
                    spec.write_value (
                        routing_info.get_first_key_from_pre_vertex (
                        self, self.inj_lnk), data_type = DataType.UINT32
                        )
        else:
            for k in range (self.NKEYS):
                spec.write_value (routing_info.get_first_key_from_pre_vertex (
                    self, self.inj_lnk[k]), data_type = DataType.UINT32)

        spec.end_specification()
