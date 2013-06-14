CC=gcc
PYFLAGS=`python-config --includes`
CFLAGS=-Wall -g ${CFLAG} -lpthread -ldl -lutil -lm -L/usr/lib/python2.6/config -lpython2.6
CFLAGS+=${PYFLAGS}
objects=libudv.o list.o

libudv.a : $(objects)
	ar -rcs libudv.a $(objects)

all: libudv.a

clean:
	rm -fr libudv.a $(objects)
