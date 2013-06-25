CROSS_COMPILE =

lib-objs := pic_ctl.o

-include config.mk

all: libpic.a test

libpic.a: $(call to-progs,$(lib-objs))
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
