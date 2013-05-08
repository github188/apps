CROSS_COMPILE =
CFLAGS = -Wall -O2 

lib-objs := pic_ctl.o

-include config.mk

#all: libpic.a test
all: test

libpic.a: $(call to-progs,$(lib-objs))
	$(QUIET_AR)

test:
	$(CROSS_COMPILE)$(CC) -o dled_test dled_test.c -L../ -lpic

$(OBJS) : %.o : %.c
	$(QUIET_CC)

.PHONY: clean test

clean::
	rm -fr dled_test
	$(call QUIET_RM,*.o *.a *.so)
