CC=gcc
#CFLAGS+=-g
CFLAGS+=-DNDEBUG
OBJECTS=log.o log-utils.o debug.o

all: liblog.a daemon

liblog.a: $(OBJECTS)
	ar -rcs liblog.a $(OBJECTS)

daemon: log-daemon.c
	gcc $(CARGS) -o log-daemon log-daemon.c -L./ -llog -lsqlite3

test: test.c
	gcc $(CARGS) -o test-log test.c -L$(PWD) -llog -lsqlite3

clean:
	rm -fr liblog.a $(OBJECTS) log-daemon test-log
