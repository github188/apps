OBJECTS = buzzer_shm.o buzzer_worker.o  main.o AlarmSW.o

all: buzzer-ctl-daemon 
ifneq ($(STRIP),)
	$(STRIP) buzzer-ctl-daemon
endif

buzzer-ctl-daemon:$(OBJECTS) 
	$(CC) -o buzzer-ctl-daemon $(OBJECTS)  $(CFLAGS) $(LDFLAGS) 


clean:
	rm -rf *.o buzzer-ctl-daemon *.a

