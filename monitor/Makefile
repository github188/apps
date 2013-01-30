CFLAGS = -Wall -O2 -DDEBUG -g
CFLAGS += -Wstrict-aliasing=0 -I/usr/include/libxml2
CFLAGS += -I/usr/include/libxml2
CFLAGS += -L../pic_ctl -lpic
CFLAGS += -std=c99
CFLAGS += -L./
#CFLAGS += -D_NDEBUG

OBJS=sys-tmpfs.o sys-global.o sys-module.o sys-action.o sys-alarm.o sys-conf.o sys-event.o list.o sys-interval-check.o sys-capture.o

all: daemon libsysmon.a
	gcc -o buzzer AlarmSW.c

daemon: $(OBJS) libsysmon.a
	gcc -o sys-mon sys-mon.c $(OBJS) -lxml2 -ljson -L../common -llog -lev -lsysmon $(CFLAGS)

libsysmon.a:
	gcc -c libsysmon.c
	ar -rcs libsysmon.a libsysmon.o

test: libsysmon.a
	gcc -o test test.c -L./ -lsysmon -ljson

test1: $(OBJS)
	gcc -o test1 test1.c $(OBJS) -lxml2 -ljson -lev -L../common -llog

clean:
	rm -fr sys-mon core $(OBJS)  libsysmon.a test buzzer test1
