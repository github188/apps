export CROSS_COMPILE ?=
export CC = $(CROSS_COMPILE)gcc
export CFLAGS = -Wall -O2
export STRIP = $(CROSS_COMPILE)strip
export AR = $(CROSS_COMPILE)ar

ifdef debug
	STRIP =
	CFLAGS = -Wall -g -DDEBUG
endif

ifdef isolated-storage
	CFLAGS += -DISOLATED_STORAGE
endif

ifdef other-hardware
	CFLAGS += -DOTHER_HARDWARE
endif

.PHONY: help clean

all:
	$(MAKE) -C common
	$(MAKE) -C udv
	$(MAKE) -C nas
	$(MAKE) -C us/md-auto-resume/mdscan
	$(MAKE) -C web-iface
ifndef other-hardware
	$(MAKE) -C pic_ctl
	$(MAKE) -C led
	$(MAKE) -C buzzer
	$(MAKE) -C monitor
	$(MAKE) -C watchdog
	$(MAKE) -C diskpower
endif
	$(MAKE) -C us
	$(MAKE) -C sys-conf

clean:
	$(MAKE) -C common clean
	$(MAKE) -C udv clean
	$(MAKE) -C nas clean
	$(MAKE) -C us/md-auto-resume/mdscan clean
	$(MAKE) -C web-iface clean
	$(MAKE) -C us clean
	$(MAKE) -C sys-conf clean
ifndef other-hardware
	$(MAKE) -C monitor clean
	$(MAKE) -C pic_ctl clean
	$(MAKE) -C sys-conf clean
	$(MAKE) -C watchdog clean
	$(MAKE) -C led clean
	$(MAKE) -C buzzer clean
	$(MAKE) -C diskpower clean
endif
	find . -name '*.pyc' -delete

help:
	@echo make [isolated-storage=1] [debug=1] [no-disk-prewarn=1] [other-hardware=1]
