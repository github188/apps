CROSS_COMPILE =

lib-objs := pic_ctl.o

-include config.mk

all: libpic.a utils test

libpic.a: $(call to-progs,$(lib-objs))
	$(QUIET_AR)

test:
	@echo "  MAKE    test"
	@make -C test

utils:
	@echo "  MAKE    utils"
	@make -C utils

$(OBJS) : %.o : %.c
	$(QUIET_CC)

.PHONY: clean test utils

clean::
	@echo "  CLEAN   test"
	@make -C test clean
	$(call QUIET_RM,*.o *.a *.so)
