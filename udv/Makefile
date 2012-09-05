CC=gcc
CFLAGS=-Wall -g
objects=libudv.o list.o

libudv.a : $(objects)
	ar -rcs libudv.a $(objects)

test: test.c libudv.c
	gcc -g -o test test.c libudv.c list.c -lparted

all: libudv.a

clean:
	rm -fr libudv.a $(objects) test test.o
