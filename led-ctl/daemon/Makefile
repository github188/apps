CC = gcc
MAKE = make
CFLAGS = -Wall -g
LDFLAGS = -lev
OBJECTS = led_shm.o led_worker.o  main.o i2c_dev.o

all: led-ctl-daemon libi2c_dev.a

led-ctl-daemon:$(OBJECTS) libi2c_dev.a
	$(CC) -o led-ctl-daemon $(OBJECTS)  $(CFLAGS) $(LDFLAGS) -L./ -li2c_dev

libi2c_dev.a: i2c_dev.o
	ar -rcs libi2c_dev.a i2c_dev.o
i2c_dev.o:
	gcc -c i2c_dev.c

clean:
	rm -rf *.o led-ctl-daemon *.a

