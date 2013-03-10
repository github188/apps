CROSS_COMPILE =
CFLAGS = -Wall -O2 

lib-objs := pic_ctl.o

-include config.mk

#all: libpic.a test
all: test

libpic.a: $(call to-progs,$(lib-objs))
	$(QUIET_AR)

test:
	@echo "  MAKE    test"
	@$(CROSS_COMPILE)$(CC) -o pic_test pic_test.c -L../ -lpic

$(OBJS) : %.o : %.c
	$(QUIET_CC)

.PHONY: clean test

clean::
	@echo "  CLEAN   test"
	@rm -fr pic_test
	$(call QUIET_RM,*.o *.a *.so)
