CFLAGS = -Wall -O2 #-g
CFLAGS += -Wstrict-aliasing=0
CFLAGS += -I/usr/include/libxml2
CFLAGS += -L../common -llog -lsqlite3
CFLAGS += -std=c99
#CFLAGS += -D_DEBUG
LDFLAGS += ../pic_ctl/libpic.a ../common/liblog.a libsysmon.a -lxml2 -ljson -lev

OBJS=sys-tmpfs.o sys-global.o sys-module.o sys-action.o sys-alarm.o sys-conf.o sys-event.o list.o sys-interval-check.o sys-capture.o util-gpio.o pmu-info.o

all: daemon libsysmon.a
	gcc -o buzzer AlarmSW.c

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
