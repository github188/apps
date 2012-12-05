#ARGS=-DNDEBUG
CFLAGS=-I/usr/include/libxml2
CFLAGS+=$(ARGS)

all:
	gcc $(CFLAGS) -o sys-mon mon-conf.c mon-capture.c sys-mon.c list.c mon-alarm.c ../common/debug.c -lxml2

clean:
	rm -fr sys-mon core* a.out *.o
