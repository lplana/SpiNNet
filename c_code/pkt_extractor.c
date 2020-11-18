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
  SYSTEM    =  0,
  EXTRACTOR =  1
};

#define TIMER_PRIORITY       0
#define EXTRACT_PRIOTITY     -1

// test exit codes
#define TEST_SUCC            0
#define CFG_FAIL             1
#define INIT_FAIL            2

#define RTR_ERRORS_ON        0x00000030
#define CC_TX_NOT_FULL       0x10000000

#define UNUSED               0
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
// packet extractor configuration - populated in SDRAM by host
typedef struct extractor_conf {
  uint32_t throttle;             // extraction slow down
  uint32_t active_time;          // length of time for packet extraction
} extractor_conf_t;

extractor_conf_t ecfg;           // extractor configuration in SDRAM

uint32_t extracted_pkts = 0;     // keep a count of extracted packets

uint32_t expected_pld = 0;       // expected payload (when used)
uint32_t missing_plds = 0;       // missing payload counter
uint32_t last_pld = 0xffffffff;  // last payload received (when used)

uint32_t end_time;               // time to end the test
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

  // extractor configuration address
  address_t sca = data_specification_get_region (EXTRACTOR, data);

  // initialise network configuration from SDRAM
  spin1_memcpy (&ecfg, sca, sizeof (extractor_conf_t));

#ifdef DEBUG_CFG
  io_printf(IO_BUF, "throttle constant = %u\n", ecfg.throttle);
  io_printf(IO_BUF, "active time = %u\n", ecfg.active_time);
#endif

  return (SUCCESS);
}
// ------------------------------------------------------------------------


// ------------------------------------------------------------------------
// initialise test variables and router
// ------------------------------------------------------------------------
uint test_init () {
  end_time = ecfg.active_time;

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
      io_printf (IO_BUF, "extracted packets: %u\n", extracted_pkts);
      io_printf (IO_BUF, "last payload rcvd: %u\n", last_pld);
      io_printf (IO_BUF, "missing payloads: %u\n", missing_plds);
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
  io_printf (IO_BUF, "<< pkt_extractor\n");

  // stop timer ticks,
  simulation_exit ();

  // and let host know that we're ready
  simulation_ready_to_read ();
}
// ------------------------------------------------------------------------


// ------------------------------------------------------------------------
// extract packets at a throttled pace
// ------------------------------------------------------------------------
void extract_packet (uint key, uint payload)
{
  (void) key;
  (void) payload;

  // count packet,
  extracted_pkts++;

  // and apply throttle control
  for (uint i = 0; i < ecfg.throttle; i++) {
    __asm__ __volatile__("");
  }
}
// ------------------------------------------------------------------------


// ------------------------------------------------------------------------
// extract packets at a throttled pace
// ------------------------------------------------------------------------
void extract_packet_with_pld (uint key, uint payload)
{
  (void) key;

  // check payload and report issues
  uint32_t diff = payload - expected_pld;

  if (diff != 0) {
    missing_plds += (diff > 0) ? diff : -diff;
  }

  // remember last payload received
  last_pld = payload;

  // update expected payload to the correct value
  expected_pld = payload + 1;

  // count packet,
  extracted_pkts++;

  // and apply throttle control
  for (uint i = 0; i < ecfg.throttle; i++) {
    __asm__ __volatile__("");
  }
}
// ------------------------------------------------------------------------


// ------------------------------------------------------------------------
// keep track of time to control test steps
// ------------------------------------------------------------------------
void time_control (uint ticks, uint null) {
  (void) null;

  // report test success and exit
  if (ticks >= end_time) {
    done (TEST_SUCC);
  }
}
// ------------------------------------------------------------------------


// ------------------------------------------------------------------------
// log initial test info
// ------------------------------------------------------------------------
void test_start (void) {
  // log in
  io_printf (IO_BUF, ">> pkt_extractor\n");
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
  spin1_callback_on (MC_PACKET_RECEIVED, extract_packet, EXTRACT_PRIOTITY);
  spin1_callback_on (MCPL_PACKET_RECEIVED, extract_packet_with_pld, EXTRACT_PRIOTITY);

  // setup simulation engine,
//lap  simulation_set_start_function (test_start);

  // and run test
  simulation_run ();
}
// ------------------------------------------------------------------------
