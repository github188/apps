CFLAGS = -Wall -O2 -DDEBUG -g
CFLAGS += -Wstrict-aliasing=0 -I/usr/include/libxml2
CFLAGS += -I/usr/include/libxml2

all:
	gcc -std=c99 -g -o sys-mon list.c sys-module.c sys-action.c sys-alarm.c sys-conf.c sys-mon.c sys-event.c $(CFLAGS) -lxml2 -ljson -lev

clean:
	rm -fr sys-mon core *.o
