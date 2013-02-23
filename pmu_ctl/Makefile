CROSS_COMPILE =
CFLAGS = -Wall -O2 

lib-objs := pmu_ctl.o

-include config.mk

all: libpmu.a test

libpmu.a: $(call to-progs,$(lib-objs))
	$(QUIET_AR)

test:
	@echo "  MAKE    test"
	@make -C test

$(OBJS) : %.o : %.c
	$(QUIET_CC)

.PHONY: clean test

clean::
	@echo "  CLEAN   test"
	@make -C test clean
	$(call QUIET_RM,*.o *.a *.so)
