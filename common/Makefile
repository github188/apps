CC=gcc
OBJECTS=log.o log-utils.o

all: liblog.a daemon

liblog.a: $(OBJECTS)
	ar -rcs liblog.a $(OBJECTS)

daemon: log-daemon.c
	gcc -o log-daemon log-daemon.c -L./ -llog -lsqlite3

test: test.c
	gcc -g -o test-log test.c -L$(PWD) -llog -lsqlite3

clean:
	rm -fr liblog.a $(OBJECTS) log-daemon test-log
