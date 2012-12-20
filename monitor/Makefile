CFLAGS+=-DNDEBUG
CFLAGS+=-I/usr/include/libxml2 -g

all:
	gcc $(CFLAGS) -o sys-mon mon-conf.c mon-capture.c sys-mon.c list.c mon-alarm.c ../common/debug.c -lxml2 -L../common -llog -lsqlite3
	gcc -o alarm AlarmSW.c

clean:
	rm -fr sys-mon core* a.out *.o
