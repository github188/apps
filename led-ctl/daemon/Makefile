OBJECTS = led_shm.o led_worker.o  main.o i2c_dev.o sysled.o

default: led-ctl-daemon sysled.o
ifneq ($(STRIP),)
	$(STRIP) led-ctl-daemon
endif

led-ctl-daemon:$(OBJECTS) sysled.o
	$(CC) -o led-ctl-daemon $(OBJECTS)  $(CFLAGS) $(LDFLAGS) 

sysled.o:
	gcc -c sysled.c

clean:
	rm -rf *.o led-ctl-daemon *.a

