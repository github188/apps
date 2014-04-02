export CFLAGS = -Wall -O2
export STRIP = strip

ifdef debug
	STRIP =
	CFLAGS = -Wall -g -DDEBUG
endif

ifdef isolated-storage
	CFLAGS += -DISOLATED_STORAGE
endif

.PHONY: help clean

all:
	$(MAKE) -C common
	$(MAKE) -C udv
	$(MAKE) -C nas
	$(MAKE) -C us/md-auto-resume/mdscan
	$(MAKE) -C web-iface
	$(MAKE) -C pic_ctl
	$(MAKE) -C led
	$(MAKE) -C buzzer
	$(MAKE) -C monitor
	$(MAKE) -C us
	$(MAKE) -C sys-conf
	$(MAKE) -C watchdog
	$(MAKE) -C diskpower
clean:
	$(MAKE) -C udv clean
	$(MAKE) -C web-iface clean
	$(MAKE) -C us clean
	$(MAKE) -C nas clean
	$(MAKE) -C us/md-auto-resume/mdscan clean
	$(MAKE) -C common clean
	$(MAKE) -C monitor clean
	$(MAKE) -C pic_ctl clean
	$(MAKE) -C sys-conf clean
	$(MAKE) -C watchdog clean
	$(MAKE) -C led clean
	$(MAKE) -C buzzer clean
	$(MAKE) -C diskpower clean
	$(MAKE) -C led-ctl clean
	$(MAKE) -C diskpw clean
	$(MAKE) -C buzzer-ctl clean
	find . -name '*.pyc' -delete

help:
	@echo make [isolated-storage=1] [debug=1]
