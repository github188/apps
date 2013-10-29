CROSS_COMPILE =

lib-objs := watchdog_lib.o

-include config.mk

all: libwatchdog.a

libwatchdog.a: $(call to-progs,$(lib-objs))
	$(QUIET_AR)


$(OBJS) : %.o : %.c
	$(QUIET_CC)

.PHONY: clean test utils

clean::
#	@echo "  CLEAN   test"
#	@make -C test clean
	$(call QUIET_RM,*.o *.a *.so)

