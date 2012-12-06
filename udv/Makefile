CC=gcc
CFLAGS=-Wall -g ${CFLAG} -I/usr/include/python2.6 -I/usr/lib/python2.6/config -lpthread -ldl -lutil -lm -lpython2.6
objects=libudv.o list.o

libudv.a : $(objects)
	ar -rcs libudv.a $(objects)

test: test.c libudv.c list.c
	gcc -g -o test test.c list.c libudv.c $(CFLAGS) -lparted

all: libudv.a

clean:
	rm -fr libudv.a $(objects) test test.o
