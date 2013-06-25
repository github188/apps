CC=gcc
CFLAGS+=-DNDEBUG
OBJECTS=log.o log-utils.o debug.o mkdir-p.o

all: liblog.a daemon

liblog.a: $(OBJECTS)
	ar -rcs liblog.a $(OBJECTS)

daemon: log-daemon.c
	gcc $(CARGS) -o log-daemon log-daemon.c liblog.a -lsqlite3
ifneq ($(STRIP),)
	$(STRIP) log-daemon
endif

test: test.c
	gcc $(CARGS) -o test-log test.c -L$(PWD) liblog.a -lsqlite3

clean:
	rm -fr liblog.a $(OBJECTS) log-daemon test-log
