CC=gcc
CFLAGS=-Wall -g ${CFLAG} -I/usr/include/python2.7 -I/usr/lib/python2.7/config -lpthread -ldl -lutil -lm -lpython2.7
objects=libudv.o list.o

libudv.a : $(objects)
	ar -rcs libudv.a $(objects)

test: test.c libudv.c
	gcc -g -o test test.c libudv.c list.c -lparted $(CFLAGS)

all: libudv.a

clean:
	rm -fr libudv.a $(objects) test test.o
