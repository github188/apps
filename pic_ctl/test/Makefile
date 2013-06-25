lib-objs := pic_ctl.o

#all: libpic.a test
all: test

libpic.a: $(call to-progs,$(lib-objs))
	$(QUIET_AR)

test:
	$(CC) $(CFLAGS) -o dled_test dled_test.c -L../ -lpic
ifneq ($(STRIP),)
	$(STRIP) dled_test
endif

$(OBJS) : %.o : %.c
	$(QUIET_CC)

.PHONY: clean test

clean::
	rm -fr dled_test
	$(call QUIET_RM,*.o *.a *.so)
