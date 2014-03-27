CFLAGS += -Wstrict-aliasing=0
CFLAGS += -I/usr/include/libxml2
CFLAGS += -std=c99
ifdef debug
CFLAGS += -D_DEBUG
endif
LDFLAGS += ../led-ctl/cmd/libled.a  ../buzzer-ctl/cmd/libbuzzer.a ../common/liblog.a libsysmon.a -lxml2 -ljson -lev -lsqlite3 -lm

OBJS=sys-tmpfs.o sys-global.o sys-module.o sys-action.o sys-alarm.o sys-conf.o sys-event.o list.o sys-interval-check.o sys-capture.o pmu-info.o

all: daemon libsysmon.a
ifneq ($(STRIP),)
	$(STRIP) sys-mon
endif

daemon: $(OBJS) libsysmon.a
	gcc -o sys-mon sys-mon.c $(OBJS) $(CFLAGS) $(LDFLAGS)

libsysmon.a:
	gcc -c libsysmon.c
	ar -rcs libsysmon.a libsysmon.o

test: libsysmon.a
	gcc -o test test.c $(LDFLAGS)

test1: $(OBJS)
	gcc -o test1 test1.c $(OBJS) $(LDFLAGS)

clean:
	rm -fr sys-mon core $(OBJS)  libsysmon.a test buzzer test1
