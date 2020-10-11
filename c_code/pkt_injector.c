// front-end-common
#include "common-typedefs.h"
#include <data_specification.h>
#include <simulation.h>

// SpiNNaker API
#include "spin1_api.h"


// ------------------------------------------------------------------------
// constants
// ------------------------------------------------------------------------
enum SDRAM_Regions {
  SYSTEM   =  0,
  INJECTOR =  1,
  ROUTING  =  2
};

#define TIMER_PRIORITY       0
#define INJECT_PRIOTITY      1

// test exit codes
#define TEST_SUCC            0
#define CFG_FAIL             1
#define INIT_FAIL            2

#define RTR_ERRORS_ON        0x00000030
#define CC_TX_NOT_FULL       0x10000000

#define UNUSED               0

#define NKEYS                32
// ------------------------------------------------------------------------


// ------------------------------------------------------------------------
// simulation engine variables
// ------------------------------------------------------------------------
static uint32_t simulation_ticks;
static uint32_t infinite_run;
static uint32_t timer_period;
static uint32_t time;
// ------------------------------------------------------------------------


// ------------------------------------------------------------------------
// global variables
// ------------------------------------------------------------------------
// packet injector configuration - populated in SDRAM by host
// packet routing keys - populated in SDRAM by host
typedef struct routing_conf {
  uint32_t nkeys;            // number of packet routing key
  uint32_t pkt_keys[NKEYS];  // packet routing keys
} routing_conf_t;

typedef struct injector_conf {
  uint32_t throttle;         // injection slow down
  uint32_t active_time;      // length of time for packet injection
  uint32_t delayed_start;    // delay the start of packet injection
  uint32_t idle_end;         // idle time after packet injection stops
} injector_conf_t;

injector_conf_t icfg;        // injector configuration in SDRAM

uint32_t nkeys;              // number of packet routing key
uint32_t * pkt_keys;          // packet routing keys

uint32_t injected_pkts = 0;  // keep a count of injected packets

uint32_t start_time;         // time to start packet injection
uint32_t stop_time;          // time to stop packet injection
uint32_t end_time;           // time to end the test

volatile uchar stop = 0;     // stop packet injection
// ------------------------------------------------------------------------


// ------------------------------------------------------------------------
// code
// ------------------------------------------------------------------------
// ------------------------------------------------------------------------
// load test configuration from SDRAM
// ------------------------------------------------------------------------
uint cfg_init (void) {
  // read the data specification header
  data_specification_metadata_t * data =
      data_specification_get_data_address ();

  // check that header is valid
  if (!data_specification_read_header (data))
  {
    return (CFG_FAIL);
  }

  // set up the simulation interface (system region)
  if (!simulation_initialise(
      data_specification_get_region(0, data), APPLICATION_NAME_HASH,
      &timer_period, &simulation_ticks, &infinite_run, &time, 0, 0)) {
    return (CFG_FAIL);
  }

  // injector configuration address
  address_t sca = data_specification_get_region (INJECTOR, data);

  // initialise configuration from SDRAM
  spin1_memcpy (&icfg, sca, sizeof (injector_conf_t));

  // routing keys address
  address_t rca = data_specification_get_region (ROUTING, data);

  // initialise routing variables from SDRAM
  routing_conf_t * rcfg = (routing_conf_t const *) rca;

  // number of routing keys
  nkeys = rcfg->nkeys;

  // allocate memory for packet routing keys
  if ((pkt_keys = ((uint32_t *)
         spin1_malloc (nkeys * sizeof (uint32_t)))) == NULL) {
    return (CFG_FAIL);
  }

  // copy packet routing keys
  spin1_memcpy (pkt_keys, rcfg->pkt_keys, nkeys * sizeof (uint32_t));

#ifdef DEBUG_CFG
  io_printf(IO_BUF, "throttle constant = %u\n", icfg.throttle);
  io_printf(IO_BUF, "active time = %u\n", icfg.active_time);
  io_printf(IO_BUF, "delayed start = %u\n", icfg.delayed_start);
  io_printf(IO_BUF, "idle end = %u\n", icfg.idle_end);
  for (uint k = 0; k < nkeys; k++) {
    io_printf(IO_BUF, "packet key[%u] = 0x%08x\n", k, pkt_keys[k]);
  }
#endif

  return (SUCCESS);
}
// ------------------------------------------------------------------------


// ------------------------------------------------------------------------
// initialise test variables and router
// ------------------------------------------------------------------------
uint test_init () {
  start_time = icfg.delayed_start;

  stop_time = start_time + icfg.active_time;

  end_time = stop_time + icfg.idle_end;

  // initialise router
  // -----------------------------
  // turn on packet error counter
  if (leadAp) {
    rtr[RTR_CONTROL] |= RTR_ERRORS_ON;
  }

  return (SUCCESS);
}
// ------------------------------------------------------------------------


// ------------------------------------------------------------------------
// check exit code and log relevant final test info
// ------------------------------------------------------------------------
void done (uint ec) {
  // report problems -- if any
  switch (ec)
  {
    case TEST_SUCC:
      io_printf (IO_BUF, "injected packets: %u\n", injected_pkts);
      io_printf (IO_BUF, "test OK\n");
      break;

    case CFG_FAIL:
      io_printf (IO_BUF, "test configuration failed\n");
      io_printf (IO_BUF, "test aborted\n");
      break;

    case INIT_FAIL:
      io_printf (IO_BUF, "test initialisation failed\n");
      io_printf (IO_BUF, "test aborted\n");
      break;
  }

  // report router dropped packets
  if (leadAp) {
    io_printf (IO_BUF, "RTR dropped MC packets: %u\n", rtr[RTR_DGC8]);
  }

  // log out
  io_printf (IO_BUF, "<< pkt_injector\n");

  // stop timer ticks,
  simulation_exit ();

  // and let host know that we're ready
  simulation_ready_to_read ();
}
// ------------------------------------------------------------------------


// ------------------------------------------------------------------------
// inject packets continuously at a throttled pace
// ------------------------------------------------------------------------
void inject_pkts (uint null0, uint null1) {
  (void) null0;
  (void) null1;

  while (!stop) {
    for (uint k = 0; k < nkeys; k++) {
      // wait until comms controller ready to transmit,
      while (!(cc[CC_TCR] & CC_TX_NOT_FULL)) {
        continue;
      }

      // fire packet,
      cc[CC_TXKEY] = pkt_keys[k];
      injected_pkts++;

      // and apply throttle control
      for (uint i = 0; i < icfg.throttle; i++) {
        __asm__ __volatile__("");
      }
    }
  }
}
// ------------------------------------------------------------------------


// ------------------------------------------------------------------------
// keep track of time to control test steps
// ------------------------------------------------------------------------
void time_control (uint ticks, uint null) {
  (void) null;

  // start sending packets
  if (ticks == start_time) {
    spin1_schedule_callback (inject_pkts, UNUSED, UNUSED, INJECT_PRIOTITY);
    return;
  }

  // stop sending packets
  if (ticks == stop_time) {
    stop = 1;
  }

  // idle time to make sure that all packets are received
  if (ticks >= end_time) {
    // report test success and exit
    done (TEST_SUCC);
  }
}
// ------------------------------------------------------------------------


// ------------------------------------------------------------------------
// log initial test info
// ------------------------------------------------------------------------
void test_start (void) {
  // log in
  io_printf (IO_BUF, ">> pkt_injector\n");
}
// ------------------------------------------------------------------------


// ------------------------------------------------------------------------
// main: initialise test, register callbacks and run test
// ------------------------------------------------------------------------
void c_main () {
  // read test configuration from SDRAM,
  uint res = cfg_init ();

  if (res != SUCCESS) {
    // report error and exit
    done (res);
  }

  // initialise test,
  res = test_init();

  if (res != SUCCESS) {
    // report error and exit
    done (res);
  }

  // set timer tick,
  spin1_set_timer_tick (timer_period);

  // register callbacks,
  spin1_callback_on (TIMER_TICK, time_control, TIMER_PRIORITY);

  // setup simulation engine,
//lap  simulation_set_start_function (test_start);

  // and run test
  simulation_run ();
}
// ------------------------------------------------------------------------
