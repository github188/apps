CFLAGS = -Wall -O2 -DDEBUG -g
CFLAGS += -Wstrict-aliasing=0 -I/usr/include/libxml2
CFLAGS += -I/usr/include/libxml2
#CFLAGS += -D_NDEBUG

all: libsysmon.a
	gcc -std=c99 -g -o sys-mon list.c sys-global.c sys-module.c sys-action.c sys-alarm.c sys-conf.c sys-mon.c sys-event.c $(CFLAGS) -lxml2 -ljson -lev
	gcc -std=c99 -g -o test test.c -L./ -lsysmon -ljson

libsysmon.a:
	gcc -c libsysmon.c
	ar -rcs libsysmon.a libsysmon.o

clean:
	rm -fr sys-mon core *.o libsysmon.a test
