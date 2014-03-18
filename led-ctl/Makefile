CFLAGS += -Wstict-aliasing=0
CFLAGS += -std=c99
ifdef debug
CFLAGS += -D_DEBUG -g -Wall
else
CFLAGS += -O2 -Wall
endif
LDFLAGS += -lev

all:daemon cmd
	$(MAKE) -C daemon
	$(MAKE) -C cmd
ifneq ($(STRIP),)
	$(STRIP) led-ctl-daemon
	$(STRIP) tools-test-led
endif

clean:
	$(MAKE) -C daemon clean
	$(MAKE) -C cmd clean
