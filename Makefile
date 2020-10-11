# The name of the application to be built

SOURCES = $(APP).c

# Directory to create APLX files in (must include trailing slash)
APP_OUTPUT_DIR = ./

SOURCE_DIRS = ./c_code

# The GFE application standard makefile
include $(SPINN_DIRS)/make/local.mk

all: $(APP_OUTPUT_DIR)$(APP).aplx

# Tidy up
tidy:
	$(RM) $(OBJECTS) $(BUILD_DIR)$(APP).elf $(BUILD_DIR)$(APP).txt
